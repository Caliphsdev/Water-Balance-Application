"""Backup Manager - handles database backup and restore operations."""
from pathlib import Path
import shutil
import os
from datetime import datetime
from typing import Optional

from utils.config_manager import config

class BackupManager:
    def __init__(self, db_path: str = None, backup_dir: str = None):
        base_dir = Path(__file__).parent.parent.parent
        if db_path is None:
            db_path = base_dir / config.get('database.path', 'data/water_balance.db')
        self.db_path = Path(db_path)

        # FIX: Always prefer a user-writable directory; fallback to LocalAppData if env missing.
        if backup_dir is None:
            user_dir = os.environ.get('WATERBALANCE_USER_DIR')
            if not user_dir:
                local_appdata = os.getenv('LOCALAPPDATA')
                if local_appdata:
                    user_dir = str(Path(local_appdata) / 'WaterBalance')
                else:
                    user_dir = str(Path.home() / '.waterbalance')
            self.backup_dir = Path(user_dir) / 'backups'
        else:
            self.backup_dir = Path(backup_dir)

        # Now safe to create directory in writable location; if it fails, fall back to user home.
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback_dir = Path.home() / '.waterbalance' / 'backups'
            fallback_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir = fallback_dir

    def create_backup(self, label: Optional[str] = None) -> Path:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = f"water_balance_{timestamp}{('_' + label) if label else ''}.db"
        dest = self.backup_dir / name
        shutil.copy2(self.db_path, dest)
        return dest

    def list_backups(self):
        return sorted(self.backup_dir.glob('water_balance_*.db'))

    def restore_backup(self, backup_file: Path):
        backup_file = Path(backup_file)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        # Simple replace
        shutil.copy2(backup_file, self.db_path)
        return self.db_path

__all__ = ["BackupManager"]
