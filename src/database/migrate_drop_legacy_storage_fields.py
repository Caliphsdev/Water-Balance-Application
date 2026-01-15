"""
Migration: drop legacy storage fields (dead_storage, siltation_percentage, low_level_alarm)

- Removes unused columns from storage_facilities
- Removes legacy LOW_LEVEL_ALARM alert rule

Run with the project venv:
    .venv\\Scripts\\python -c "import sys; sys.path.insert(0, 'src'); import database.migrate_drop_legacy_storage_fields as m; m.main()"
"""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).parent.parent.parent
DB_CANDIDATES = [
    ROOT / "data" / "water_balance.db",
    ROOT / "data" / "water_balance.db.new",
]
LEGACY_COLUMNS = ["dead_storage", "siltation_percentage", "low_level_alarm"]
LEGACY_ALERT = "LOW_LEVEL_ALARM"


def _sqlite_version_ok(cursor) -> bool:
    cursor.execute("select sqlite_version()")
    version = cursor.fetchone()[0]
    major, minor, patch = (int(x) for x in version.split("."))
    return (major, minor, patch) >= (3, 35, 0)


def migrate():
    db_path = next((p for p in DB_CANDIDATES if p.exists()), None)
    if db_path is None:
        raise FileNotFoundError(f"Database not found. Checked: {', '.join(str(p) for p in DB_CANDIDATES)}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        if not _sqlite_version_ok(cursor):
            raise RuntimeError("SQLite 3.35+ required for DROP COLUMN. Please upgrade SQLite or rebuild the DB with schema.py.")

        cursor.execute("PRAGMA foreign_keys=OFF;")
        cursor.execute("PRAGMA writable_schema=1;")

        # Identify existing columns
        cursor.execute("PRAGMA table_info(storage_facilities)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        to_drop = [c for c in LEGACY_COLUMNS if c in existing_cols]

        if to_drop:
            for col in to_drop:
                print(f"Dropping column: {col}")
                cursor.execute(f"ALTER TABLE storage_facilities DROP COLUMN {col}")
        else:
            print("No legacy storage columns to drop.")

        # Remove legacy alert rule if present
        cursor.execute("DELETE FROM alert_rules WHERE rule_code = ?", (LEGACY_ALERT,))
        if cursor.rowcount:
            print(f"Removed alert rule: {LEGACY_ALERT}")
        else:
            print("Legacy alert rule not present (already clean).")

        conn.commit()
        print("✅ Migration completed successfully.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.execute("PRAGMA writable_schema=0;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        conn.close()


def main():
    migrate()


if __name__ == "__main__":
    main()
