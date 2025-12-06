#!/usr/bin/env python3
"""Check inter-area transfer bidirectional flags."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "water_balance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get overall stats
cur.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN is_bidirectional=1 THEN 1 ELSE 0 END) as bidirectional,
        SUM(CASE WHEN flow_type='dirty' THEN 1 ELSE 0 END) as dirty_flows
    FROM wb_inter_area_transfers
""")
row = cur.fetchone()
print(f"Total inter-area transfers: {row[0]}")
print(f"Bidirectional: {row[1]}")
print(f"Dirty flows: {row[2]}")

# Check dirty flows with bidirectional flag
cur.execute("""
    SELECT COUNT(*) 
    FROM wb_inter_area_transfers 
    WHERE flow_type='dirty' AND is_bidirectional=1
""")
dirty_bidi = cur.fetchone()[0]
print(f"Dirty + bidirectional: {dirty_bidi}")

# Check if any dirty flows are NOT bidirectional
cur.execute("""
    SELECT COUNT(*) 
    FROM wb_inter_area_transfers 
    WHERE flow_type='dirty' AND is_bidirectional=0
""")
dirty_not_bidi = cur.fetchone()[0]
print(f"Dirty + NOT bidirectional: {dirty_not_bidi}")

if dirty_not_bidi == 0:
    print("\n✅ All dirty inter-area transfers are bidirectional!")
else:
    print(f"\n⚠️  {dirty_not_bidi} dirty inter-area transfers are NOT bidirectional")
    cur.execute("""
        SELECT a1.area_code, a2.area_code, s1.structure_code, s2.structure_code, iat.subcategory, iat.notes
        FROM wb_inter_area_transfers iat
        JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
        JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
        JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
        JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
        WHERE iat.flow_type='dirty' AND iat.is_bidirectional=0
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} / {row[2]} → {row[1]} / {row[3]} | {row[4]} | {row[5]}")

conn.close()
