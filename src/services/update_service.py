"""
Update Service

Handles application updates including:
- Checking for tier-specific updates from Supabase
- Downloading updates from GitHub releases
- Auto-rollback on failed updates
- Database backup preservation

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable

from PySide6.QtCore import QObject, Signal, QThread

from core.supabase_client import (
    get_supabase_client, 
    SupabaseClient,
    SupabaseError,
    SupabaseConnectionError
)
from services.license_service import get_license_service
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


# (CONSTANTS)

# Current app version (fallback if config is unavailable)
APP_VERSION = "0.0.0"

# Update check interval in seconds (1 day)
UPDATE_CHECK_INTERVAL = 86400

# Download timeout in seconds
DOWNLOAD_TIMEOUT = 300

# Backup retention (number of backups to keep)
BACKUP_RETENTION = 3


# (UPDATE INFO)

class UpdateInfo:
    """Information about an available update."""
    
    def __init__(
        self,
        version: str,
        tier: str,
        download_url: str,
        release_notes: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        checksum_sha256: Optional[str] = None,
        is_critical: bool = False
    ):
        self.version = version
        self.tier = tier
        self.download_url = download_url
        self.release_notes = release_notes
        self.file_size_bytes = file_size_bytes
        self.checksum_sha256 = checksum_sha256
        self.is_critical = is_critical
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateInfo':
        """Create UpdateInfo from Supabase row."""
        file_size = data.get("file_size_bytes")
        if file_size is None:
            file_size = data.get("file_size")

        checksum = data.get("checksum_sha256")
        if checksum is None:
            checksum = data.get("file_hash")

        is_critical = data.get("is_critical")
        if is_critical is None:
            is_critical = data.get("is_mandatory", False)

        return cls(
            version=data["version"],
            tier=data.get("tier", "unknown"),
            download_url=data["download_url"],
            release_notes=data.get("release_notes"),
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            is_critical=is_critical
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "tier": self.tier,
            "download_url": self.download_url,
            "release_notes": self.release_notes,
            "file_size_bytes": self.file_size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "is_critical": self.is_critical
        }
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in MB."""
        if self.file_size_bytes:
            return round(self.file_size_bytes / (1024 * 1024), 1)
        return None


class UpdateStatus:
    """Status of an update operation."""
    
    CHECKING = "checking"
    AVAILABLE = "available"
    NO_UPDATE = "no_update"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    
    def __init__(
        self,
        status: str,
        message: str = "",
        progress: int = 0,
        update_info: Optional[UpdateInfo] = None,
        error: Optional[str] = None
    ):
        self.status = status
        self.message = message
        self.progress = progress  # 0-100
        self.update_info = update_info
        self.error = error


# (DOWNLOAD WORKER)

class DownloadWorker(QObject):
    """Worker for downloading updates in background."""
    
    progress = Signal(int, int)  # bytes_downloaded, total_bytes
    finished = Signal(str)  # local_path
    error = Signal(str)
    
    def __init__(self, url: str, dest_path: str, expected_checksum: Optional[str] = None):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self.expected_checksum = expected_checksum
        self._cancelled = False
    
    def cancel(self):
        """Cancel the download."""
        self._cancelled = True
    
    def run(self):
        """Download the file."""
        try:
            logger.info(f"Starting download from {self.url}")
            
            # Create request
            request = urllib.request.Request(
                self.url,
                headers={"User-Agent": f"WaterBalance/{APP_VERSION}"}
            )
            
            # Open connection
            with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                # Initialize hash if checksum provided
                sha256 = hashlib.sha256() if self.expected_checksum else None
                
                # Download in chunks
                with open(self.dest_path, 'wb') as f:
                    while not self._cancelled:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        if sha256:
                            sha256.update(chunk)
                        
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)
                
                if self._cancelled:
                    # Clean up partial download
                    if os.path.exists(self.dest_path):
                        os.remove(self.dest_path)
                    self.error.emit("Download cancelled")
                    return
                
                # Verify checksum
                if sha256 and self.expected_checksum:
                    actual_checksum = sha256.hexdigest()
                    if actual_checksum.lower() != self.expected_checksum.lower():
                        os.remove(self.dest_path)
                        self.error.emit(
                            f"Checksum mismatch: expected {self.expected_checksum[:16]}..., "
                            f"got {actual_checksum[:16]}..."
                        )
                        return
                    logger.debug("Checksum verified")
                
                logger.info(f"Download complete: {self.dest_path}")
                self.finished.emit(self.dest_path)
                
        except urllib.error.URLError as e:
            logger.error(f"Download failed: {e}")
            self.error.emit(f"Download failed: {e.reason}")
        except Exception as e:
            logger.error(f"Download error: {e}")
            self.error.emit(f"Download error: {e}")


# (UPDATE SERVICE)

class UpdateService(QObject):
    """
    Service for managing application updates.
    
    Features:
    - Tier-specific update checking
    - Background downloading
    - Pre-update database backup
    - Auto-rollback on failure
    """
    
    # Signals
    update_available = Signal(object)  # UpdateInfo
    update_progress = Signal(int, str)  # progress 0-100, message
    update_completed = Signal()
    update_failed = Signal(str)  # error message
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        supabase_client: Optional[SupabaseClient] = None
    ):
        super().__init__()
        
        self._data_dir = data_dir
        self._supabase = supabase_client
        config = ConfigManager()
        self._current_version = str(config.get("app.version", APP_VERSION))
        self._download_thread: Optional[QThread] = None
        self._download_worker: Optional[DownloadWorker] = None
        self._last_check: Optional[datetime] = None
        self._cached_update: Optional[UpdateInfo] = None
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
            
            self._initialized = True
    
    @property
    def current_version(self) -> str:
        """Get current app version."""
        return self._current_version
    
    @property
    def db_path(self) -> Path:
        """Get path to main database."""
        self._ensure_initialized()
        return self._data_dir / "water_balance.db"
    
    @property
    def backup_dir(self) -> Path:
        """Get backup directory."""
        self._ensure_initialized()
        return self._data_dir / "backups"
    
    # (VERSION COMPARISON)
    
    def _parse_version(self, version: str) -> tuple:
        """Parse version string to comparable tuple."""
        try:
            parts = version.lstrip('v').split('.')
            return tuple(int(p) for p in parts[:3])
        except (ValueError, IndexError):
            return (0, 0, 0)
    
    def _is_newer_version(self, version: str) -> bool:
        """Check if version is newer than current."""
        current = self._parse_version(self._current_version)
        new = self._parse_version(version)
        return new > current
    
    # (UPDATE CHECKING)
    
    def check_for_updates(self, force: bool = False) -> Optional[UpdateInfo]:
        """
        Check for available updates.
        
        Args:
            force: Force check even if recently checked.
            
        Returns:
            UpdateInfo if update available, None otherwise.
        """
        self._ensure_initialized()
        
        # Rate limit checks
        if not force and self._last_check:
            elapsed = (datetime.now(timezone.utc) - self._last_check).total_seconds()
            if elapsed < UPDATE_CHECK_INTERVAL and self._cached_update is not None:
                return self._cached_update
        
        try:
            # Get user's license tier
            license_service = get_license_service()
            tier = license_service.get_tier()
            
            if not tier:
                logger.warning("No license tier - cannot check updates")
                return None
            
            logger.info(f"Checking for updates (tier: {tier}, current: {self._current_version})")
            
            # Query Supabase for latest update for this tier
            result = self._supabase.select_contains(
                table="app_updates",
                column="min_tiers",
                values=[tier],
                order="published_at.desc",
                limit=1
            )
            
            self._last_check = datetime.now(timezone.utc)
            
            if not result:
                logger.debug("No updates found")
                self._cached_update = None
                return None
            
            update_data = result[0]
            
            # Check if newer than current
            if not self._is_newer_version(update_data["version"]):
                logger.debug(f"Current version {self._current_version} is up to date")
                self._cached_update = None
                return None
            
            # Create UpdateInfo
            update_info = UpdateInfo.from_dict(update_data)
            self._cached_update = update_info
            
            logger.info(f"Update available: {update_info.version}")
            self.update_available.emit(update_info)
            
            return update_info
            
        except SupabaseConnectionError as e:
            logger.warning(f"Cannot check for updates (offline): {e}")
            return None
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return None
    
    # (BACKUP)
    
    def create_backup(self) -> Optional[Path]:
        """
        Create backup of database before update.
        
        Returns:
            Path to backup file or None if failed.
        """
        self._ensure_initialized()
        
        if not self.db_path.exists():
            logger.debug("No database to backup")
            return None
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_name = f"water_balance.backup-{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # Copy database
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            
            # Clean old backups
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """Remove old backups keeping only BACKUP_RETENTION most recent."""
        try:
            backups = sorted(
                self.backup_dir.glob("water_balance.backup-*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for old_backup in backups[BACKUP_RETENTION:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup.name}")
                
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file.
            
        Returns:
            True if restored successfully.
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            # Remove current database
            if self.db_path.exists():
                self.db_path.unlink()
            
            # Copy backup to database location
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    # (DOWNLOAD)
    
    def download_update(
        self,
        update_info: UpdateInfo,
        callback: Optional[Callable[[int, str], None]] = None
    ) -> None:
        """
        Download update in background.
        
        Args:
            update_info: The update to download.
            callback: Progress callback (progress_percent, message).
        """
        self._ensure_initialized()
        
        # Create temp directory for download
        temp_dir = Path(tempfile.gettempdir()) / "waterbalance_update"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename from URL
        filename = update_info.download_url.split('/')[-1]
        if not filename:
            filename = f"WaterBalance-{update_info.version}-Setup.exe"
        
        dest_path = temp_dir / filename
        
        # Cancel existing download
        self.cancel_download()
        
        # Start download in thread
        self._download_thread = QThread()
        self._download_worker = DownloadWorker(
            url=update_info.download_url,
            dest_path=str(dest_path),
            expected_checksum=update_info.checksum_sha256
        )
        self._download_worker.moveToThread(self._download_thread)
        
        # Connect signals
        self._download_thread.started.connect(self._download_worker.run)
        
        def on_progress(downloaded, total):
            if total > 0:
                percent = int((downloaded / total) * 100)
                msg = f"Downloading... {downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB"
            else:
                percent = 0
                msg = f"Downloading... {downloaded // 1024 // 1024}MB"
            
            self.update_progress.emit(percent, msg)
            if callback:
                callback(percent, msg)
        
        def on_finished(local_path):
            self.update_progress.emit(100, "Download complete")
            self._on_download_complete(local_path, update_info)
        
        def on_error(error):
            self.update_failed.emit(error)
        
        self._download_worker.progress.connect(on_progress)
        self._download_worker.finished.connect(on_finished)
        self._download_worker.error.connect(on_error)
        self._download_worker.finished.connect(self._download_thread.quit)
        self._download_worker.error.connect(self._download_thread.quit)
        
        logger.info(f"Starting download: {update_info.download_url}")
        self._download_thread.start()
    
    def cancel_download(self):
        """Cancel ongoing download."""
        if self._download_worker:
            self._download_worker.cancel()
        if self._download_thread and self._download_thread.isRunning():
            self._download_thread.quit()
            self._download_thread.wait(5000)
    
    def _on_download_complete(self, local_path: str, update_info: UpdateInfo):
        """Handle completed download."""
        logger.info(f"Download complete: {local_path}")
        
        # Save update info for installation
        info_path = Path(local_path).parent / "update_info.json"
        with open(info_path, 'w') as f:
            json.dump({
                "installer_path": local_path,
                "version": update_info.version,
                "tier": update_info.tier
            }, f)
        
        self.update_progress.emit(100, f"Update {update_info.version} ready to install")
    
    # (INSTALLATION)
    
    def install_update(self, installer_path: str) -> bool:
        """
        Install downloaded update with auto-rollback.
        
        Args:
            installer_path: Path to installer executable.
            
        Returns:
            True if installation started (app will close).
        """
        self._ensure_initialized()
        
        if not os.path.exists(installer_path):
            self.update_failed.emit(f"Installer not found: {installer_path}")
            return False
        
        logger.info(f"Starting installation: {installer_path}")
        
        # Create backup before installation
        backup_path = self.create_backup()
        if backup_path:
            logger.info(f"Pre-update backup created: {backup_path}")
        
        try:
            # Launch installer
            # The installer should handle the update process
            # App will close and installer takes over
            
            if sys.platform == "win32":
                # Windows: Launch installer with elevated privileges
                subprocess.Popen(
                    [installer_path, "/SILENT", "/CLOSEAPPLICATIONS"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.Popen([installer_path])
            
            self.update_completed.emit()
            return True
            
        except Exception as e:
            error_msg = f"Failed to launch installer: {e}"
            logger.error(error_msg)
            
            # Attempt rollback if backup exists
            if backup_path and backup_path.exists():
                logger.info("Attempting rollback...")
                if self.restore_backup(backup_path):
                    self.update_failed.emit(f"{error_msg}. Database restored from backup.")
                else:
                    self.update_failed.emit(f"{error_msg}. Rollback also failed!")
            else:
                self.update_failed.emit(error_msg)
            
            return False
    
    def check_pending_update(self) -> Optional[Dict]:
        """
        Check if there's a downloaded update ready to install.
        
        Returns:
            Update info dict or None.
        """
        temp_dir = Path(tempfile.gettempdir()) / "waterbalance_update"
        info_path = temp_dir / "update_info.json"
        
        if info_path.exists():
            try:
                with open(info_path, 'r') as f:
                    info = json.load(f)
                
                if os.path.exists(info.get("installer_path", "")):
                    return info
            except Exception as e:
                logger.debug(f"Could not read pending update info: {e}")
        
        return None
    
    def clear_pending_update(self):
        """Clear pending update files."""
        temp_dir = Path(tempfile.gettempdir()) / "waterbalance_update"
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.debug("Cleared pending update")
            except Exception as e:
                logger.warning(f"Could not clear pending update: {e}")


# (SINGLETON)

_service_instance: Optional[UpdateService] = None


def get_update_service() -> UpdateService:
    """
    Get the singleton UpdateService instance.
    
    Returns:
        UpdateService instance.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = UpdateService()
    return _service_instance


# (MODULE TEST)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    app = QApplication(sys.argv)
    
    logger.info("Update Service Test")
    logger.info("=" * 50)
    
    service = get_update_service()
    
    logger.info("Current version: %s", service.current_version)
    logger.info("Database path: %s", service.db_path)
    logger.info("Backup dir: %s", service.backup_dir)

    logger.info("")
    logger.info("Checking for updates...")
    update = service.check_for_updates(force=True)
    
    if update:
        logger.info("Update available: %s", update.version)
        logger.info("Download URL: %s", update.download_url)
        logger.info("Critical: %s", update.is_critical)
    else:
        logger.info("No updates available")
    
    sys.exit(0)
