from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "water_balance.db"

KEY_COLS = (
    "from_structure_id",
    "to_structure_id",
    "flow_type",
    "subcategory",
    "is_bidirectional",
    "is_internal",
)


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def dedup_and_index():
    conn = connect()
    try:
        cur = conn.cursor()
        key_expr = ", ".join(KEY_COLS)
        cur.execute(f"""
            SELECT {key_expr}, COUNT(*) AS cnt
            FROM wb_flow_connections
            GROUP BY {key_expr}
            HAVING cnt > 1
        """)
        duplicates = cur.fetchall()
        removed = 0
        for dup in duplicates:
            where = " AND ".join([f"{col} = ?" for col in KEY_COLS])
            params = dup[:len(KEY_COLS)]
            cur.execute(f"SELECT connection_id FROM wb_flow_connections WHERE {where} ORDER BY connection_id ASC", params)
            ids = [r[0] for r in cur.fetchall()]
            for cid in ids[1:]:
                cur.execute("DELETE FROM wb_flow_connections WHERE connection_id = ?", (cid,))
                removed += 1
        conn.commit()
        # Add unique index to prevent future duplicates
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uniq_wb_flow_connections_key
            ON wb_flow_connections (
                from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal
            )
            """
        )
        conn.commit()
        print(f"Dedup complete. Removed {removed} duplicate flow connection rows.")
    finally:
        conn.close()


if __name__ == "__main__":
    dedup_and_index()
