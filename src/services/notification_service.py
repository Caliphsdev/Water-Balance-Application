"""
Notification Service

Handles syncing and managing notifications from Supabase.
Supports tier-based filtering and offline caching.

Threading: Uses QRunnable + QThreadPool following PySide6 best practices.
See: Docs/pyside6/create-gui-applications-pyside6.pdf Chapter 7

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import os
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from PySide6.QtCore import QObject, Signal, QTimer, QRunnable, QThreadPool, Slot

from core.hwid import get_hwid
from core.supabase_client import (
    get_supabase_client, 
    SupabaseClient,
    SupabaseError,
    SupabaseConnectionError
)
from services.license_service import get_license_service

logger = logging.getLogger(__name__)


# (WORKER SIGNALS - Separate QObject for QRunnable signals)

class NotificationSyncSignals(QObject):
    """
    Signals for NotificationSyncWorker.
    
    Since QRunnable doesn't inherit QObject, we need a separate
    QObject to hold the signals. This is the standard pattern
    from PySide6 documentation.
    """
    finished = Signal()
    error = Signal(str)
    result = Signal(list, int)  # (notifications, unread_count)


class NotificationSyncWorker(QRunnable):
    """
    Worker to sync notifications in background thread.
    
    Uses QThreadPool for thread management, which is the
    recommended approach for PySide6 applications.
    """
    
    def __init__(self, service: 'NotificationService'):
        super().__init__()
        self.service = service
        self.signals = NotificationSyncSignals()

    def _safe_emit(self, signal, *args) -> bool:
        """Emit a signal if the receiver still exists."""
        try:
            signal.emit(*args)
            return True
        except RuntimeError:
            return False
    
    @Slot()
    def run(self):
        """
        Perform sync in background thread.
        
        Signals are emitted to communicate results back to main thread.
        This is thread-safe because Qt handles signal delivery across threads.
        """
        try:
            # Ensure service is initialized (thread-safe)
            self.service._ensure_initialized()
            
            # Get license tier
            license_service = get_license_service()
            tier = license_service.get_tier()
            
            if not tier:
                logger.debug("No license tier - using cached notifications")
                if self._safe_emit(
                    self.signals.result,
                    self.service._notifications,
                    self.service.unread_count,
                ):
                    self._safe_emit(self.signals.finished)
                return
            
            logger.debug(f"Background sync: fetching notifications for tier '{tier}'")
            
            # Fetch from Supabase (this is the blocking network call)
            supabase = self.service._supabase
            
            result = supabase.select_contains(
                table="notifications",
                column="target_tiers",
                values=[tier]
            )
            
            # Fetch read status
            read_result = supabase.select(
                table="notification_reads",
                filters={"hwid": self.service.hwid}
            )
            
            read_notification_ids = {r["notification_id"] for r in read_result}
            
            # Process notifications
            new_notifications = []
            for row in result:
                is_read = row["id"] in read_notification_ids or row["id"] in self.service._read_ids
                notif = Notification.from_dict(row, is_read=is_read)
                new_notifications.append(notif)
            
            # Sort by date (newest first)
            new_notifications.sort(key=lambda n: n.created_at or datetime.min, reverse=True)
            
            # Update service state (thread-safe assignment)
            self.service._notifications = new_notifications
            self.service._read_ids.update(read_notification_ids)
            self.service._last_sync = datetime.now(timezone.utc)
            
            # Save cache (file I/O in background thread - good!)
            self.service._save_cache()
            
            unread = sum(1 for n in new_notifications if not n.is_read)
            logger.info(f"Background sync complete: {len(new_notifications)} notifications, {unread} unread")
            
            # Emit result signal - Qt will deliver this to main thread
            if self._safe_emit(self.signals.result, new_notifications, unread):
                self._safe_emit(self.signals.finished)
            
        except SupabaseConnectionError as e:
            logger.warning(f"Notification sync failed (offline): {e}")
            if self._safe_emit(self.signals.error, "Offline - using cached notifications"):
                self._safe_emit(self.signals.finished)
        except Exception as e:
            logger.error(f"Notification sync error: {e}")
            if self._safe_emit(self.signals.error, str(e)):
                self._safe_emit(self.signals.finished)


# (CONSTANTS)

# Sync interval in milliseconds (3 hours)
SYNC_INTERVAL_MS = 3 * 60 * 60 * 1000

# Cache file name
NOTIFICATIONS_CACHE_FILE = "notifications_cache.json"

# Maximum notifications to cache
MAX_CACHED_NOTIFICATIONS = 100


# (NOTIFICATION MODEL)

class Notification:
    """Represents a notification message."""
    
    TYPE_ANNOUNCEMENT = "announcement"
    TYPE_RELEASE_NOTES = "release_notes"
    TYPE_MAINTENANCE = "maintenance"
    TYPE_LICENSE_WARNING = "license_warning"
    TYPE_FEATURE_PREVIEW = "feature_preview"
    
    def __init__(
        self,
        id: str,
        title: str,
        body: str,
        type: str = TYPE_ANNOUNCEMENT,
        target_tiers: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        is_read: bool = False
    ):
        self.id = id
        self.title = title
        self.body = body
        self.type = type
        self.target_tiers = target_tiers or ['developer', 'premium', 'standard', 'free_trial']
        self.created_at = created_at or datetime.now(timezone.utc)
        self.is_read = is_read
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], is_read: bool = False) -> 'Notification':
        """Create Notification from Supabase row."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            title=data["title"],
            body=data["body"],
            type=data.get("type", cls.TYPE_ANNOUNCEMENT),
            target_tiers=data.get("target_tiers"),
            created_at=created_at,
            is_read=is_read
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "type": self.type,
            "target_tiers": self.target_tiers,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_read": self.is_read
        }
    
    @property
    def age_display(self) -> str:
        """Get human-readable age string."""
        if not self.created_at:
            return ""
        
        now = datetime.now(timezone.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        
        delta = now - created
        
        if delta.days > 30:
            return f"{delta.days // 30}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "Just now"
    
    @property
    def is_new(self) -> bool:
        """Check if notification is less than 2 days old and unread."""
        if self.is_read:
            return False
        
        if not self.created_at:
            return True
        
        now = datetime.now(timezone.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        
        return (now - created) < timedelta(days=2)
    
    @property
    def type_icon(self) -> str:
        """Get icon for notification type."""
        icons = {
            self.TYPE_ANNOUNCEMENT: "📢",
            self.TYPE_RELEASE_NOTES: "🆕",
            self.TYPE_MAINTENANCE: "🔧",
            self.TYPE_LICENSE_WARNING: "⚠️",
            self.TYPE_FEATURE_PREVIEW: "✨"
        }
        return icons.get(self.type, "📬")


# (NOTIFICATION SERVICE)

class NotificationService(QObject):
    """
    Service for managing notifications.
    
    Features:
    - Syncs notifications from Supabase
    - Filters by user's license tier
    - Caches notifications locally for offline access
    - Tracks read status
    - Periodic background sync
    """
    
    # Signals
    notifications_updated = Signal(list)  # List[Notification]
    new_notification = Signal(object)  # Notification
    unread_count_changed = Signal(int)
    sync_error = Signal(str)
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        supabase_client: Optional[SupabaseClient] = None
    ):
        super().__init__()
        
        self._data_dir = data_dir
        self._supabase = supabase_client
        self._notifications: List[Notification] = []
        self._read_ids: set = set()
        self._deleted_ids: set = set()
        self._sync_timer: Optional[QTimer] = None
        self._last_sync: Optional[datetime] = None
        self._init_lock = threading.Lock()
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """Ensure service is initialized."""
        if self._initialized:
            return
        
        with self._init_lock:
            if self._initialized:
                return
            
            # Set up data directory
            if self._data_dir is None:
                user_dir = os.environ.get('WATERBALANCE_USER_DIR', '')
                if user_dir:
                    self._data_dir = Path(user_dir) / "data"
                else:
                    self._data_dir = Path(__file__).parent.parent.parent / "data"
            
            self._data_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up Supabase client
            if self._supabase is None:
                self._supabase = get_supabase_client()
            
            # Load cached notifications
            self._load_cache()
            
            self._initialized = True
            logger.debug(f"Notification service initialized")
    
    @property
    def cache_file_path(self) -> Path:
        """Get path to cache file."""
        self._ensure_initialized()
        return self._data_dir / NOTIFICATIONS_CACHE_FILE
    
    @property
    def hwid(self) -> str:
        """Get hardware ID for read tracking."""
        return get_hwid()
    
    # (CACHE OPERATIONS)
    
    def _load_cache(self) -> None:
        """Load notifications from cache file."""
        # Access _data_dir directly to avoid calling cache_file_path property
        # which would recursively call _ensure_initialized() causing a deadlock
        cache_path = self._data_dir / NOTIFICATIONS_CACHE_FILE
        if not cache_path.exists():
            return
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._notifications = [
                Notification.from_dict(n, is_read=n.get("is_read", False))
                for n in data.get("notifications", [])
            ]
            self._read_ids = set(data.get("read_ids", []))
            self._deleted_ids = set(data.get("deleted_ids", []))
            
            # Update read status from read_ids
            for notif in self._notifications:
                if notif.id in self._read_ids:
                    notif.is_read = True
            
            logger.debug(f"Loaded {len(self._notifications)} notifications from cache")
            
        except Exception as e:
            logger.warning(f"Failed to load notification cache: {e}")
    
    def _save_cache(self) -> None:
        """Save notifications to cache file."""
        try:
            data = {
                "notifications": [n.to_dict() for n in self._notifications[:MAX_CACHED_NOTIFICATIONS]],
                "read_ids": list(self._read_ids),
                "deleted_ids": list(self._deleted_ids),
                "last_sync": self._last_sync.isoformat() if self._last_sync else None
            }
            
            # Access _data_dir directly to avoid potential deadlock
            cache_path = self._data_dir / NOTIFICATIONS_CACHE_FILE
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Notification cache saved")
            
        except Exception as e:
            logger.warning(f"Failed to save notification cache: {e}")
    
    # (SYNC)
    
    def sync(self, force: bool = False) -> List[Notification]:
        """
        Sync notifications from Supabase.
        
        Args:
            force: Force sync even if recently synced.
            
        Returns:
            List of notifications.
        """
        self._ensure_initialized()
        
        # Get user's tier
        license_service = get_license_service()
        tier = license_service.get_tier()
        
        if not tier:
            logger.debug("No license tier - using cached notifications")
            return self._notifications
        
        try:
            logger.debug(f"Syncing notifications for tier: {tier}")
            
            # Fetch notifications from Supabase
            # Using contains query for target_tiers array
            result = self._supabase.select_contains(
                table="notifications",
                column="target_tiers",
                values=[tier]
            )
            
            # Also fetch read status
            read_result = self._supabase.select(
                table="notification_reads",
                filters={"hwid": self.hwid}
            )
            
            read_notification_ids = {r["notification_id"] for r in read_result}
            
            # Process notifications
            old_ids = {n.id for n in self._notifications}
            new_notifications = []
            
            for row in result:
                if row["id"] in self._deleted_ids:
                    continue
                is_read = row["id"] in read_notification_ids or row["id"] in self._read_ids
                notif = Notification.from_dict(row, is_read=is_read)
                new_notifications.append(notif)
                
                # Check for new notifications
                if row["id"] not in old_ids and not is_read:
                    self.new_notification.emit(notif)
            
            # Sort by date (newest first)
            new_notifications.sort(key=lambda n: n.created_at or datetime.min, reverse=True)
            
            # Update state
            self._notifications = new_notifications
            self._read_ids.update(read_notification_ids)
            self._last_sync = datetime.now(timezone.utc)
            
            # Save to cache
            self._save_cache()
            
            # Emit signals
            self.notifications_updated.emit(self._notifications)
            self.unread_count_changed.emit(self.unread_count)
            
            logger.info(f"Synced {len(self._notifications)} notifications, {self.unread_count} unread")
            
            return self._notifications
            
        except SupabaseConnectionError as e:
            logger.warning(f"Cannot sync notifications (offline): {e}")
            self.sync_error.emit("Offline - using cached notifications")
            return self._notifications
        except Exception as e:
            logger.error(f"Notification sync failed: {e}")
            self.sync_error.emit(str(e))
            return self._notifications
    
    def start_background_sync(self) -> None:
        """
        Start periodic background sync using QThreadPool.
        
        This follows PySide6 best practices:
        - QThreadPool manages thread lifecycle
        - QRunnable workers perform network I/O
        - Signals deliver results to main thread safely
        """
        if self._sync_timer is not None:
            return
        
        # Create thread pool if not exists
        if not hasattr(self, '_threadpool'):
            self._threadpool = QThreadPool.globalInstance()
            logger.debug(f"Using QThreadPool with {self._threadpool.maxThreadCount()} threads")
        
        # Set up periodic timer
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._start_sync_worker)
        self._sync_timer.start(SYNC_INTERVAL_MS)
        
        # Initial sync after 2 seconds (gives app time to fully load)
        QTimer.singleShot(2000, self._start_sync_worker)
        
        logger.debug("Background notification sync scheduled (QThreadPool)")
    
    def _start_sync_worker(self) -> None:
        """
        Start a sync worker on the thread pool.
        
        This runs in the main thread - it just queues work on the pool.
        """
        worker = NotificationSyncWorker(self)
        worker.signals.result.connect(self._on_sync_result)
        worker.signals.error.connect(self._on_sync_error)
        self._threadpool.start(worker)
    
    @Slot(list, int)
    def _on_sync_result(self, notifications: List[Notification], unread_count: int) -> None:
        """
        Handle sync result from worker (runs in main thread).
        
        This slot receives the signal from the worker and updates the UI.
        Qt guarantees this runs in the main thread.
        """
        self.notifications_updated.emit(notifications)
        self.unread_count_changed.emit(unread_count)
    
    @Slot(str)
    def _on_sync_error(self, error_msg: str) -> None:
        """
        Handle sync error from worker (runs in main thread).
        """
        self.sync_error.emit(error_msg)
    
    def _safe_sync(self) -> None:
        """Perform sync with error handling to prevent crashes."""
        try:
            self.sync()
        except Exception as e:
            logger.error(f"Background sync error: {e}")
    
    def stop_background_sync(self) -> None:
        """Stop periodic background sync."""
        if self._sync_timer:
            self._sync_timer.stop()
            self._sync_timer = None
            logger.debug("Background notification sync stopped")
    
    # (READ STATUS)
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: The notification ID.
            
        Returns:
            True if marked successfully.
        """
        self._ensure_initialized()
        
        # Update local state
        self._read_ids.add(notification_id)
        
        for notif in self._notifications:
            if notif.id == notification_id:
                notif.is_read = True
                break
        
        # Save to cache
        self._save_cache()
        
        # Try to sync to Supabase
        try:
            # Use upsert to handle duplicates gracefully
            # If the record already exists, it will just update it (no-op)
            self._supabase.upsert(
                table="notification_reads",
                data={
                    "notification_id": notification_id,
                    "hwid": self.hwid
                }
            )
        except Exception as e:
            # Even if sync fails, the local cache is already updated
            logger.debug(f"Could not sync read status to Supabase: {e}")
        
        self.unread_count_changed.emit(self.unread_count)
        return True

    def mark_as_deleted(self, notification_id: str) -> bool:
        """Hide a notification locally for this device."""
        self._ensure_initialized()

        self._deleted_ids.add(notification_id)
        self._read_ids.add(notification_id)

        self._notifications = [n for n in self._notifications if n.id != notification_id]

        self._save_cache()
        self.unread_count_changed.emit(self.unread_count)
        return True
    
    def mark_all_as_read(self) -> None:
        """Mark all notifications as read."""
        for notif in self._notifications:
            if not notif.is_read:
                self.mark_as_read(notif.id)
    
    # (ACCESSORS)
    
    @property
    def notifications(self) -> List[Notification]:
        """Get all notifications."""
        self._ensure_initialized()
        return self._notifications
    
    @property
    def unread_notifications(self) -> List[Notification]:
        """Get unread notifications."""
        return [n for n in self._notifications if not n.is_read]
    
    @property
    def unread_count(self) -> int:
        """Get count of unread notifications."""
        return len(self.unread_notifications)
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        for notif in self._notifications:
            if notif.id == notification_id:
                return notif
        return None
    
    def get_cached_notifications(self) -> List[Dict[str, Any]]:
        """Get all cached notifications as dictionaries (CACHE ACCESS).
        
        Returns notifications from the in-memory cache without
        triggering a sync. Useful for displaying notifications
        quickly in the UI.
        
        Returns:
            List of notification dictionaries with keys:
            - id, title, message, type, created_at, is_read
        """
        self._ensure_initialized()
        return [n.to_dict() for n in self._notifications if n.id not in self._deleted_ids]


# (SINGLETON)

_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Get the singleton NotificationService instance.
    
    Returns:
        NotificationService instance.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = NotificationService()
    return _service_instance


# (MODULE TEST)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    app = QApplication(sys.argv)
    
    logger.info("Notification Service Test")
    logger.info("=" * 50)
    
    service = get_notification_service()
    
    logger.info("Cache file: %s", service.cache_file_path)
    logger.info("HWID: %s...", service.hwid[:16])

    logger.info("")
    logger.info("Syncing notifications...")
    notifications = service.sync(force=True)
    
    logger.info("Total: %s", len(notifications))
    logger.info("Unread: %s", service.unread_count)
    
    for n in notifications[:5]:
        logger.info("  %s %s (%s) %s", n.type_icon, n.title, n.age_display, "NEW" if n.is_new else "")
    
    sys.exit(0)
