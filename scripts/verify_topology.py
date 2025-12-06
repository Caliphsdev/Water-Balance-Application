"""
Verify and display topology for all seeded areas.
Use this to review structures, flows, inflows, outflows, and inter-area transfers.
"""

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'water_balance.db'


def verify_area(area_code: str, db_path: Path = DB_PATH):
    """Display complete topology for a given area."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        
        # Get area info
        cur.execute("SELECT * FROM wb_areas WHERE area_code=?", (area_code,))
        area = cur.fetchone()
        if not area:
            print(f"❌ Area '{area_code}' not found.")
            return
        
        area_id = area['area_id']
        print(f"\n{'='*80}")
        print(f"AREA: {area['area_name']} ({area['area_code']})")
        print(f"{'='*80}\n")
        
        # Structures
        cur.execute("""
            SELECT structure_code, structure_name, structure_type, is_group, notes
            FROM wb_structures
            WHERE area_id=?
            ORDER BY structure_type, structure_code
        """, (area_id,))
        structures = cur.fetchall()
        print(f"📦 STRUCTURES ({len(structures)}):")
        for s in structures:
            group_mark = " [GROUP]" if s['is_group'] else ""
            print(f"  • {s['structure_code']:20} | {s['structure_name']:35} | {s['structure_type']:15}{group_mark}")
        
        # Inflows
        print(f"\n⬇️  INFLOWS (External sources):")
        cur.execute("""
            SELECT i.source_code, i.source_name, i.source_type, s.structure_code, i.notes
            FROM wb_inflow_sources i
            JOIN wb_structures s ON i.target_structure_id = s.structure_id
            WHERE s.area_id=?
            ORDER BY i.source_type, i.source_code
        """, (area_id,))
        inflows = cur.fetchall()
        if inflows:
            for inf in inflows:
                print(f"  • {inf['source_code']:25} ({inf['source_type']:10}) → {inf['structure_code']:20} | {inf['source_name']}")
        else:
            print("  (none)")
        
        # Internal flows
        print(f"\n🔄 INTERNAL FLOWS:")
        cur.execute("""
            SELECT f.flow_type, f.subcategory, f.is_bidirectional, f.is_internal,
                   s1.structure_code as from_code, s2.structure_code as to_code, f.notes
            FROM wb_flow_connections f
            JOIN wb_structures s1 ON f.from_structure_id = s1.structure_id
            JOIN wb_structures s2 ON f.to_structure_id = s2.structure_id
            WHERE s1.area_id=? OR s2.area_id=?
            ORDER BY f.flow_type, s1.structure_code
        """, (area_id, area_id))
        flows = cur.fetchall()
        if flows:
            for fl in flows:
                bidir = " ↔" if fl['is_bidirectional'] else " →"
                internal = " [INTERNAL]" if fl['is_internal'] else ""
                subcat = f" ({fl['subcategory']})" if fl['subcategory'] else ""
                print(f"  • {fl['from_code']:20}{bidir} {fl['to_code']:20} | {fl['flow_type']:6}{subcat}{internal}")
        else:
            print("  (none)")
        
        # Outflows
        print(f"\n⬆️  OUTFLOWS (System exits):")
        cur.execute("""
            SELECT o.destination_code, o.destination_name, o.destination_type, s.structure_code, o.notes
            FROM wb_outflow_destinations o
            JOIN wb_structures s ON o.source_structure_id = s.structure_id
            WHERE s.area_id=?
            ORDER BY o.destination_type, o.destination_code
        """, (area_id,))
        outflows = cur.fetchall()
        if outflows:
            for out in outflows:
                print(f"  • {out['structure_code']:20} → {out['destination_code']:30} ({out['destination_type']:12}) | {out['destination_name']}")
        else:
            print("  (none)")
        
        # Inter-area transfers OUT
        print(f"\n🌐 INTER-AREA TRANSFERS (Outgoing from this area):")
        cur.execute("""
            SELECT t.flow_type, t.subcategory, 
                   s1.structure_code as from_code, 
                   a2.area_code as to_area, s2.structure_code as to_code,
                   t.notes
            FROM wb_inter_area_transfers t
            JOIN wb_areas a2 ON t.to_area_id = a2.area_id
            LEFT JOIN wb_structures s1 ON t.from_structure_id = s1.structure_id
            LEFT JOIN wb_structures s2 ON t.to_structure_id = s2.structure_id
            WHERE t.from_area_id=?
            ORDER BY t.flow_type, a2.area_code
        """, (area_id,))
        out_transfers = cur.fetchall()
        if out_transfers:
            for tr in out_transfers:
                from_s = tr['from_code'] or "(area-level)"
                to_s = tr['to_code'] or "(area-level)"
                subcat = f" ({tr['subcategory']})" if tr['subcategory'] else ""
                print(f"  • {from_s:20} → {tr['to_area']:15} / {to_s:20} | {tr['flow_type']:6}{subcat}")
                if tr['notes']:
                    print(f"      └─ {tr['notes']}")
        else:
            print("  (none)")
        
        # Inter-area transfers IN
        print(f"\n🌐 INTER-AREA TRANSFERS (Incoming to this area):")
        cur.execute("""
            SELECT t.flow_type, t.subcategory,
                   a1.area_code as from_area, s1.structure_code as from_code,
                   s2.structure_code as to_code,
                   t.notes
            FROM wb_inter_area_transfers t
            JOIN wb_areas a1 ON t.from_area_id = a1.area_id
            LEFT JOIN wb_structures s1 ON t.from_structure_id = s1.structure_id
            LEFT JOIN wb_structures s2 ON t.to_structure_id = s2.structure_id
            WHERE t.to_area_id=?
            ORDER BY t.flow_type, a1.area_code
        """, (area_id,))
        in_transfers = cur.fetchall()
        if in_transfers:
            for tr in in_transfers:
                from_s = tr['from_code'] or "(area-level)"
                to_s = tr['to_code'] or "(area-level)"
                subcat = f" ({tr['subcategory']})" if tr['subcategory'] else ""
                print(f"  • {tr['from_area']:15} / {from_s:20} → {to_s:20} | {tr['flow_type']:6}{subcat}")
                if tr['notes']:
                    print(f"      └─ {tr['notes']}")
        else:
            print("  (none)")
        
        print(f"\n{'='*80}\n")
        
    finally:
        conn.close()


def list_all_areas(db_path: Path = DB_PATH):
    """List all seeded areas."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT area_code, area_name FROM wb_areas ORDER BY area_id")
        areas = cur.fetchall()
        print("\n📋 ALL SEEDED AREAS:")
        for a in areas:
            print(f"  • {a['area_code']:15} - {a['area_name']}")
        print()
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        area_code = sys.argv[1].upper()
        verify_area(area_code)
    else:
        list_all_areas()
        print("Usage: python verify_topology.py <AREA_CODE>")
        print("Example: python verify_topology.py UG2_NORTH")
