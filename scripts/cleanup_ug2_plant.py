from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'water_balance.db'

def cleanup_ug2_plant(db_path: Path = DB_PATH):
    conn = sqlite3.connect(str(db_path))
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        cur = conn.cursor()
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ('UG2_PLANT',))
        row = cur.fetchone()
        if not row:
            print('UG2_PLANT area not found; nothing to clean.')
            return
        area_id = row[0]
        # Collect structures
        cur.execute("SELECT structure_id FROM wb_structures WHERE area_id=?", (area_id,))
        sids = [r[0] for r in cur.fetchall()]
        for sid in sids:
            cur.execute("DELETE FROM wb_flow_connections WHERE from_structure_id=? OR to_structure_id=?", (sid, sid))
            cur.execute("DELETE FROM wb_inflow_sources WHERE target_structure_id=?", (sid,))
            cur.execute("DELETE FROM wb_outflow_destinations WHERE source_structure_id=?", (sid,))
            cur.execute("DELETE FROM wb_inter_area_transfers WHERE from_structure_id=? OR to_structure_id=?", (sid, sid))
        cur.execute("DELETE FROM wb_inter_area_transfers WHERE from_area_id=? OR to_area_id=?", (area_id, area_id))
        cur.execute("DELETE FROM wb_structures WHERE area_id=?", (area_id,))
        cur.execute("DELETE FROM wb_areas WHERE area_id=?", (area_id,))
        conn.commit()
        print('UG2_PLANT cleanup complete.')
    finally:
        conn.close()

if __name__ == '__main__':
    cleanup_ug2_plant()
