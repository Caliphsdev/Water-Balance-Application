"""
SQLite Migration Manager

Applies ordered SQLite migrations from data/sqlite_migrations.
Tracks applied files in schema_migrations table.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Set

from core.config_manager import get_resource_path
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MigrationManager:
    """Apply pending SQLite migrations in a safe, ordered way."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        migrations_dir: Optional[Path] = None
    ) -> None:
        self.db_path = db_path or DatabaseManager().db_path
        self.migrations_dir = migrations_dir or self._resolve_migrations_dir()

    def _resolve_migrations_dir(self) -> Path:
        """Resolve migrations directory from user data or packaged resources."""
        user_dir = os.environ.get("WATERBALANCE_USER_DIR", "")
        if user_dir:
            user_path = Path(user_dir) / "data" / "sqlite_migrations"
            if user_path.exists():
                return user_path
        return get_resource_path("data/sqlite_migrations")

    def apply_pending(self) -> List[str]:
        """Apply all pending migrations and return applied filenames."""
        if not self.migrations_dir.exists():
            logger.info(
                "SQLite migrations directory not found: %s",
                self.migrations_dir
            )
            return []

        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        if not migration_files:
            logger.info("No SQLite migrations found in %s", self.migrations_dir)
            return []

        applied: List[str] = []
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._ensure_migrations_table(conn)
            applied_set = self._get_applied_migrations(conn)
            pending = [m for m in migration_files if m.name not in applied_set]
            if pending and self.db_path.exists():
                DatabaseManager(self.db_path).create_backup()

            for migration_path in pending:
                if migration_path.name in applied_set:
                    continue

                sql = migration_path.read_text(encoding="utf-8")
                try:
                    conn.execute("BEGIN")
                    conn.executescript(sql)
                    conn.execute(
                        "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)",
                        (migration_path.name, datetime.utcnow().isoformat())
                    )
                    conn.commit()
                    applied.append(migration_path.name)
                    logger.info("Applied SQLite migration: %s", migration_path.name)
                except Exception as exc:
                    conn.rollback()
                    logger.error(
                        "SQLite migration failed (%s): %s",
                        migration_path.name,
                        exc
                    )
                    raise

            return applied
        finally:
            conn.close()

    @staticmethod
    def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
        """Create schema_migrations table if it does not exist."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                applied_at TEXT NOT NULL
            )
            """
        )

    @staticmethod
    def _get_applied_migrations(conn: sqlite3.Connection) -> Set[str]:
        """Return a set of applied migration filenames."""
        cursor = conn.execute(
            "SELECT filename FROM schema_migrations ORDER BY id"
        )
        return {row[0] for row in cursor.fetchall()}
