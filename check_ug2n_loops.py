import sqlite3

try:
    conn = sqlite3.connect('data/water_balance.db')
    cursor = conn.cursor()
    
    # Find UG2 North structures
    cursor.execute("""
        SELECT 
            s.structure_code,
            s.structure_name,
            s.structure_type,
            a.area_name
        FROM wb_structures s
        JOIN wb_areas a ON s.area_id = a.area_id
        WHERE a.area_code LIKE '%UG2%NORTH%' OR a.area_name LIKE '%UG2%North%'
        ORDER BY s.structure_code
    """)
    
    structures = cursor.fetchall()
    
    print("="*100)
    print("UG2 NORTH STRUCTURES")
    print("="*100)
    print(f"\nFound {len(structures)} structures:\n")
    
    for code, name, struct_type, area in structures:
        print(f"  {code:20s} - {name:40s} ({struct_type})")
    
    # Check for self-loops in UG2 North
    cursor.execute("""
        SELECT 
            s.structure_code,
            s.structure_name,
            fc.flow_type,
            fc.subcategory,
            fc.notes
        FROM wb_flow_connections fc
        JOIN wb_structures s ON fc.from_structure_id = s.structure_id
        JOIN wb_areas a ON s.area_id = a.area_id
        WHERE (a.area_code LIKE '%UG2%NORTH%' OR a.area_name LIKE '%UG2%North%')
          AND fc.from_structure_id = fc.to_structure_id
    """)
    
    ug2n_loops = cursor.fetchall()
    
    print("\n" + "="*100)
    print("UG2 NORTH SELF-LOOPS")
    print("="*100)
    print(f"\nFound {len(ug2n_loops)} self-loops:\n")
    
    if ug2n_loops:
        for code, name, flow_type, subcategory, notes in ug2n_loops:
            print(f"  {code:20s} - {name}")
            print(f"    Type: {flow_type} ({subcategory})")
            print(f"    Notes: {notes or 'N/A'}\n")
    else:
        print("  ⚠️ No self-loops found for UG2 North structures")
        print("  This might need to be added to the database topology")
    
    conn.close()
    print("\n✅ Check complete")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
