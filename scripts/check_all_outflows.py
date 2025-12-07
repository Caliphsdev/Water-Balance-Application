#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check ALL areas' outflows from database to verify template."""
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

DB_PATH = Path(__file__).parent.parent / "data" / "water_balance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 120)
print("ALL AREAS - ACTUAL OUTFLOWS FROM DATABASE")
print("=" * 120)

# Get all areas
cur.execute("SELECT area_id, area_code, area_name FROM wb_areas ORDER BY area_code")
areas = cur.fetchall()

for area_id, area_code, area_name in areas:
    print(f"\n{'=' * 120}")
    print(f"AREA: {area_code} - {area_name}")
    print(f"{'=' * 120}")
    
    # Get structures in this area
    print(f"\nSTRUCTURES IN {area_code}:")
    print("-" * 120)
    cur.execute("""
        SELECT structure_code, structure_name, structure_type
        FROM wb_structures
        WHERE area_id = ?
        ORDER BY structure_code
    """, (area_id,))
    
    structures = cur.fetchall()
    if structures:
        for code, name, stype in structures:
            print(f"  {code:20} | {name:45} | {stype:15}")
    else:
        print("  (No structures)")
    
    # Get internal outflows
    print(f"\nINTERNAL OUTFLOWS (leaving {area_code} structures):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            s1.structure_code, s2.structure_code,
            fc.flow_type, fc.subcategory,
            fc.is_bidirectional, fc.notes
        FROM wb_flow_connections fc
        JOIN wb_structures s1 ON fc.from_structure_id = s1.structure_id
        JOIN wb_structures s2 ON fc.to_structure_id = s2.structure_id
        WHERE s1.area_id = ?
        ORDER BY s1.structure_code, s2.structure_code
    """, (area_id,))
    
    flows = cur.fetchall()
    if flows:
        for row in flows:
            from_code, to_code, flow_type, subcat, is_bidi, notes = row
            bidi = " ↔" if is_bidi else " →"
            subcat_str = subcat if subcat else "N/A"
            print(f"  {from_code:20}{bidi} {to_code:20} | {flow_type:15} ({subcat_str:20})")
    else:
        print("  (No internal outflows)")
    
    # Get inter-area outflows
    print(f"\nINTER-AREA OUTFLOWS (TO other areas):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            s1.structure_code, a2.area_code, s2.structure_code,
            iat.flow_type, iat.subcategory,
            iat.is_bidirectional, iat.notes
        FROM wb_inter_area_transfers iat
        JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
        JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
        JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
        WHERE iat.from_area_id = ?
        ORDER BY a2.area_code, s2.structure_code
    """, (area_id,))
    
    transfers = cur.fetchall()
    if transfers:
        for row in transfers:
            from_code, to_area, to_code, flow_type, subcat, is_bidi, notes = row
            bidi = " ↔" if is_bidi else " →"
            subcat_str = subcat if subcat else "N/A"
            print(f"  {from_code:20}{bidi} {to_area}/{to_code:20} | {flow_type:15} ({subcat_str:20})")
    else:
        print("  (No inter-area outflows)")

conn.close()

print("\n" + "=" * 120)
print("ANALYSIS COMPLETE - Use this to verify OUTFLOW_CODES_TEMPLATE.txt")
print("=" * 120)
