from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "water_balance.db"

KEY_COLS = (
    "from_area_id",
    "to_area_id",
    "from_structure_id",
    "to_structure_id",
    "flow_type",
    "subcategory",
)


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def dedup_and_index():
    conn = connect()
    try:
        cur = conn.cursor()
        # Find duplicate groups by key cols
        key_expr = ", ".join(KEY_COLS)
        cur.execute(f"""
            SELECT {key_expr}, COUNT(*) AS cnt
            FROM wb_inter_area_transfers
            GROUP BY {key_expr}
            HAVING cnt > 1
        """)
        duplicates = cur.fetchall()
        removed = 0
        for dup in duplicates:
            # Build where clause for the key
            where = " AND ".join([f"{col} = ?" for col in KEY_COLS])
            params = dup[:len(KEY_COLS)]
            # Fetch all matching rows ordered by transfer_id ascending
            cur.execute(f"SELECT transfer_id FROM wb_inter_area_transfers WHERE {where} ORDER BY transfer_id ASC", params)
            rows = [r[0] for r in cur.fetchall()]
            # Keep the first, delete the rest
            for tid in rows[1:]:
                cur.execute("DELETE FROM wb_inter_area_transfers WHERE transfer_id = ?", (tid,))
                removed += 1
        conn.commit()
        # Create a unique index to prevent future duplicates
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uniq_wb_inter_area_transfers_key
            ON wb_inter_area_transfers (
                from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory
            )
            """
        )
        conn.commit()
        print(f"Dedup complete. Removed {removed} duplicate inter-area transfer rows.")
    finally:
        conn.close()


if __name__ == "__main__":
    dedup_and_index()
