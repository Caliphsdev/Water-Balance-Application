import sqlite3

try:
    conn = sqlite3.connect('data/water_balance.db')
    cursor = conn.cursor()
    
    # Find self-loops: flows where from_structure_id = to_structure_id
    cursor.execute("""
        SELECT 
            s.structure_code,
            s.structure_name,
            a.area_name,
            fc.flow_type,
            fc.subcategory,
            fc.notes
        FROM wb_flow_connections fc
        JOIN wb_structures s ON fc.from_structure_id = s.structure_id
        JOIN wb_areas a ON s.area_id = a.area_id
        WHERE fc.from_structure_id = fc.to_structure_id
        ORDER BY a.area_name, s.structure_code
    """)
    
    self_loops = cursor.fetchall()
    
    print("="*100)
    print("DAM SELF-LOOPS (Recirculation within same dam)")
    print("="*100)
    print(f"\nFound {len(self_loops)} self-loop connections:\n")
    
    if self_loops:
        current_area = None
        for structure_code, structure_name, area_name, flow_type, subcategory, notes in self_loops:
            if area_name != current_area:
                print(f"\n{'='*100}")
                print(f"📍 {area_name}")
                print(f"{'='*100}")
                current_area = area_name
            
            print(f"\n  {structure_code:20s} ({structure_name})")
            print(f"    Flow Type:  {flow_type}")
            print(f"    Subcategory: {subcategory}")
            print(f"    Notes: {notes or 'N/A'}")
    else:
        print("\n⚠️  No self-loops found in database.")
        print("\nThis might mean:")
        print("1. Self-loops aren't registered yet in wb_flow_connections")
        print("2. They're tracked differently in the system")
        print("3. They need to be added to the topology")
    
    # Also check for bidirectional internal flows
    print("\n" + "="*100)
    print("BIDIRECTIONAL INTERNAL FLOWS (within same area)")
    print("="*100)
    
    cursor.execute("""
        SELECT 
            s1.structure_code as from_code,
            s2.structure_code as to_code,
            s1.structure_name as from_name,
            s2.structure_name as to_name,
            a.area_name,
            fc.flow_type,
            fc.subcategory,
            fc.is_bidirectional,
            fc.notes
        FROM wb_flow_connections fc
        JOIN wb_structures s1 ON fc.from_structure_id = s1.structure_id
        JOIN wb_structures s2 ON fc.to_structure_id = s2.structure_id
        JOIN wb_areas a ON s1.area_id = a.area_id
        WHERE fc.is_internal = 1 
          AND fc.is_bidirectional = 1
          AND s1.area_id = s2.area_id
        ORDER BY a.area_name, s1.structure_code
    """)
    
    bidirectional = cursor.fetchall()
    print(f"\nFound {len(bidirectional)} bidirectional internal flows:\n")
    
    current_area = None
    for from_code, to_code, from_name, to_name, area_name, flow_type, subcategory, is_bi, notes in bidirectional:
        if area_name != current_area:
            print(f"\n{'='*100}")
            print(f"📍 {area_name}")
            print(f"{'='*100}")
            current_area = area_name
        
        print(f"\n  {from_code} ↔ {to_code}")
        print(f"    From: {from_name}")
        print(f"    To: {to_name}")
        print(f"    Type: {flow_type} ({subcategory})")
        print(f"    Notes: {notes or 'N/A'}")
    
    conn.close()
    print("\n✅ Database check complete")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
