#!/usr/bin/env python3
"""Show all inflows for each area and prepare for temporary value input."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "water_balance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 120)
print("WATER BALANCE INFLOWS BY AREA - READY FOR VALUE INPUT")
print("=" * 120)

cur.execute("SELECT area_id, area_code, area_name FROM wb_areas ORDER BY area_code")
areas = cur.fetchall()

all_inflows = {}

for area_id, area_code, area_name in areas:
    print(f"\n{'=' * 120}")
    print(f"📍 AREA: {area_code} - {area_name}")
    print(f"{'=' * 120}")
    
    # Get external inflows (rainfall, boreholes, rivers, ore water, etc.)
    print(f"\n⬇️  EXTERNAL INFLOWS (from nature/extraction):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            iso.inflow_id,
            s.structure_code,
            s.structure_name,
            iso.source_type,
            iso.source_code,
            iso.source_name,
            iso.notes
        FROM wb_inflow_sources iso
        JOIN wb_structures s ON iso.target_structure_id = s.structure_id
        WHERE s.area_id = ?
        ORDER BY iso.source_type, s.structure_code
    """, (area_id,))
    
    external_inflows = cur.fetchall()
    inflow_dict = {}
    
    if external_inflows:
        for row in external_inflows:
            inflow_id, struct_code, struct_name, source_type, source_code, source_name, notes = row
            key = f"{source_code} ({source_type})"
            inflow_dict[key] = {
                'target': struct_code,
                'target_name': struct_name,
                'source': source_name,
                'notes': notes,
                'inflow_id': inflow_id
            }
            print(f"  {source_code:20} ({source_type:12}) → {struct_code:12} ({struct_name:30}) | {source_name}")
    else:
        print("  (No external inflows)")
    
    # Get inter-area inflows
    print(f"\n🌐 INTER-AREA INFLOWS (from other areas):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            iat.transfer_id,
            a1.area_code,
            s1.structure_code,
            s1.structure_name,
            s2.structure_code,
            s2.structure_name,
            iat.flow_type,
            iat.subcategory,
            iat.is_bidirectional,
            iat.notes
        FROM wb_inter_area_transfers iat
        JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
        JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
        JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
        WHERE iat.to_area_id = ?
        ORDER BY a1.area_code, s1.structure_code
    """, (area_id,))
    
    interarea_inflows = cur.fetchall()
    
    if interarea_inflows:
        for row in interarea_inflows:
            transfer_id, from_area, from_struct, from_struct_name, to_struct, to_struct_name, flow_type, subcategory, is_bidi, notes = row
            bidi_marker = " ↔ (bidirectional)" if is_bidi else ""
            inflow_dict[f"{from_area}/{from_struct}"] = {
                'target': to_struct,
                'target_name': to_struct_name,
                'source': f"{from_area}/{from_struct}",
                'notes': notes,
                'transfer_id': transfer_id,
                'flow_type': flow_type
            }
            print(f"  {from_area}/{from_struct:12} → {to_struct:12} ({to_struct_name:30}) | {flow_type} ({subcategory}){bidi_marker}")
    else:
        print("  (No inter-area inflows)")
    
    # Get internal inflows (from other structures in same area)
    print(f"\n↔️  INTERNAL INFLOWS (from other structures in {area_code}):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            fc.connection_id,
            s1.structure_code,
            s1.structure_name,
            s2.structure_code,
            s2.structure_name,
            fc.flow_type,
            fc.subcategory,
            fc.is_bidirectional,
            fc.notes
        FROM wb_flow_connections fc
        JOIN wb_structures s1 ON fc.from_structure_id = s1.structure_id
        JOIN wb_structures s2 ON fc.to_structure_id = s2.structure_id
        WHERE s1.area_id = ? AND s2.area_id = ? AND fc.is_internal = 1
        ORDER BY s1.structure_code, s2.structure_code
    """, (area_id, area_id))
    
    internal_inflows = cur.fetchall()
    
    if internal_inflows:
        for row in internal_inflows:
            connection_id, from_struct, from_struct_name, to_struct, to_struct_name, flow_type, subcategory, is_bidi, notes = row
            bidi_marker = " ↔ (bidirectional)" if is_bidi else ""
            inflow_dict[f"{from_struct}→{to_struct}"] = {
                'target': to_struct,
                'target_name': to_struct_name,
                'source': from_struct,
                'notes': notes,
                'connection_id': connection_id,
                'flow_type': flow_type
            }
            print(f"  {from_struct:12} → {to_struct:12} ({to_struct_name:30}) | {flow_type} ({subcategory}){bidi_marker}")
    else:
        print("  (No internal inflows)")
    
    all_inflows[area_code] = inflow_dict

print("\n\n" + "=" * 120)
print("TEMPLATE FOR INPUT VALUES")
print("=" * 120)
print("\nProvide inflow values in m³ for each source. Format:")
print("  AREA_CODE[SOURCE_CODE] = VALUE")
print("\nExample:")
print("  UG2_NORTH[UG2N_NDCD_rainfall] = 5000")
print("  UG2_NORTH[UG2N_NDCDG] = 25000 (inter-area transfer from dam)")
print("  MER_PLANT[MPGWA_boreholes] = 3500")
print("\nReady to accept your inflow values for each area...")

conn.close()
