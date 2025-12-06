#!/usr/bin/env python3
"""List all inflow source codes for each area for value input."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "water_balance.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT area_id, area_code, area_name FROM wb_areas ORDER BY area_code")
areas = cur.fetchall()

print("\n" + "=" * 100)
print("INFLOW SOURCE CODES BY AREA - FILL IN YOUR VALUES")
print("=" * 100)

for area_id, area_code, area_name in areas:
    print(f"\n{'=' * 100}")
    print(f"📍 {area_code} - {area_name}")
    print("=" * 100)
    
    # External inflows (rainfall, boreholes, rivers, ore)
    cur.execute("""
        SELECT source_code, source_name, source_type
        FROM wb_inflow_sources iso
        JOIN wb_structures s ON iso.target_structure_id = s.structure_id
        WHERE s.area_id = ?
        ORDER BY source_type, source_code
    """, (area_id,))
    
    external = cur.fetchall()
    if external:
        print("\n⬇️  EXTERNAL INFLOWS (nature/extraction):")
        for src_code, src_name, src_type in external:
            print(f"  {src_code:35} ({src_type:12}) = _____ m³  # {src_name}")
    
    # Inter-area inflows
    cur.execute("""
        SELECT 
            a1.area_code || '/' || s1.structure_code as from_code,
            a1.area_name,
            iat.flow_type,
            iat.is_bidirectional
        FROM wb_inter_area_transfers iat
        JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
        JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
        WHERE iat.to_area_id = ?
        ORDER BY from_code
    """, (area_id,))
    
    interarea = cur.fetchall()
    if interarea:
        print("\n🌐 INTER-AREA INFLOWS (from other areas):")
        for from_code, from_area, flow_type, is_bidi in interarea:
            bidi_mark = " [BIDIRECTIONAL - can be +/- value]" if is_bidi else ""
            print(f"  {from_code:35} ({flow_type:12}) = _____ m³  # From {from_area}{bidi_mark}")
    
    if not external and not interarea:
        print("\n  (No direct external or inter-area inflows)")

print("\n" + "=" * 100)
print("NOTES:")
print("=" * 100)
print("• External inflows = rainfall, boreholes, rivers, ore water (from nature)")
print("• Inter-area inflows = transfers from other areas")
print("• [BIDIRECTIONAL] = value can be positive (inflow) or negative (outflow)")
print("• Internal flows (within same area) are calculated from structure connections")
print("\nFill in the _____ with your m³ values for each inflow source.")

conn.close()
