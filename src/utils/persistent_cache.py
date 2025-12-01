"""
Persistent cache for Excel facility-month results.

Stores serialized JSON blobs keyed by (excel_path, facility_code, year, month)
with an excel_sig (mtime:size) to invalidate on file changes.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional, Tuple


class ExcelStorageCache:
    def __init__(self, cache_path: Path):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.cache_path.as_posix())

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS excel_storage_cache (
                    excel_path TEXT NOT NULL,
                    facility_code TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    excel_sig TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (excel_path, facility_code, year, month)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_sig ON excel_storage_cache (excel_path, excel_sig)"
            )

    def get(self, excel_path: str, facility_code: str, year: int, month: int, excel_sig: str) -> Optional[dict]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT data_json, excel_sig FROM excel_storage_cache
                WHERE excel_path = ? AND facility_code = ? AND year = ? AND month = ?
                """,
                (excel_path, facility_code, year, month),
            )
            row = cur.fetchone()
            if not row:
                return None
            data_json, stored_sig = row
            if stored_sig != excel_sig:
                return None
            try:
                return json.loads(data_json)
            except Exception:
                return None

    def set(self, excel_path: str, facility_code: str, year: int, month: int, excel_sig: str, data: dict):
        payload = json.dumps(data, separators=(",", ":"))
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO excel_storage_cache (excel_path, facility_code, year, month, excel_sig, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(excel_path, facility_code, year, month) DO UPDATE SET
                    excel_sig=excluded.excel_sig,
                    data_json=excluded.data_json,
                    updated_at=excluded.updated_at
                """,
                (excel_path, facility_code, year, month, excel_sig, payload, now, now),
            )

    def purge_for_excel(self, excel_path: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM excel_storage_cache WHERE excel_path = ?", (excel_path,))
