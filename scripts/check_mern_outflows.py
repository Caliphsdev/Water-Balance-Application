#!/usr/bin/env python3
"""Check actual outflows for MER_NORTH from database."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "water_balance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 100)
print("MER_NORTH ACTUAL OUTFLOWS FROM DATABASE")
print("=" * 100)

# Get MER_NORTH area_id
cur.execute("SELECT area_id FROM wb_areas WHERE area_code = 'MER_NORTH'")
area_id = cur.fetchone()[0]

print("\n1. INTERNAL FLOW CONNECTIONS (within or leaving MER_NORTH):")
print("-" * 100)
cur.execute("""
    SELECT 
        s1.structure_code, s1.structure_name,
        s2.structure_code, s2.structure_name,
        fc.flow_type, fc.subcategory, 
        fc.is_bidirectional,
        fc.notes
    FROM wb_flow_connections fc
    JOIN wb_structures s1 ON fc.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON fc.to_structure_id = s2.structure_id
    WHERE s1.area_id = ?
    ORDER BY s1.structure_code
""", (area_id,))

flows = cur.fetchall()
if flows:
    for row in flows:
        from_code, from_name, to_code, to_name, flow_type, subcat, is_bidi, notes = row
        bidi = " ↔ (bidirectional)" if is_bidi else ""
        subcat_str = subcat if subcat else "N/A"
        print(f"  {from_code:15} → {to_code:15} | {flow_type:15} ({subcat_str:20}){bidi}")
        print(f"    {notes if notes else '(no notes)'}")
else:
    print("  (No internal flow connections)")

print("\n2. INTER-AREA TRANSFERS FROM MER_NORTH:")
print("-" * 100)
cur.execute("""
    SELECT 
        a1.area_code, s1.structure_code, s1.structure_name,
        a2.area_code, s2.structure_code, s2.structure_name,
        iat.flow_type, iat.subcategory,
        iat.is_bidirectional,
        iat.notes
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
    WHERE a1.area_code = 'MER_NORTH'
    ORDER BY a2.area_code, s2.structure_code
""")

transfers = cur.fetchall()
if transfers:
    for row in transfers:
        from_area, from_code, from_name, to_area, to_code, to_name, flow_type, subcat, is_bidi, notes = row
        bidi = " ↔ (bidirectional)" if is_bidi else ""
        subcat_str = subcat if subcat else "N/A"
        print(f"  {from_area}/{from_code:15} → {to_area}/{to_code:15} | {flow_type:15} ({subcat_str:20}){bidi}")
        print(f"    {notes if notes else '(no notes)'}")
else:
    print("  (No inter-area transfers)")

print("\n3. STRUCTURES IN MER_NORTH:")
print("-" * 100)
cur.execute("""
    SELECT 
        structure_code, structure_name, structure_type,
        notes
    FROM wb_structures
    WHERE area_id = ?
    ORDER BY structure_code
""", (area_id,))

structures = cur.fetchall()
if structures:
    for row in structures:
        code, name, stype, notes = row
        print(f"  {code:15} | {name:40} | {stype:15}")
        if notes:
            print(f"    Notes: {notes}")
else:
    print("  (No structures)")

conn.close()

print("\n" + "=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
