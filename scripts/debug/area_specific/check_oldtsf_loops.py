import sqlite3

try:
    conn = sqlite3.connect('data/water_balance.db')
    cursor = conn.cursor()
    
    # Find OLD_TSF area
    cursor.execute("SELECT area_id FROM wb_areas WHERE area_code = 'OLD_TSF'")
    area_result = cursor.fetchone()
    
    if not area_result:
        print("❌ OLD_TSF area not found")
        conn.close()
        exit(1)
    
    area_id = area_result[0]
    
    # Find all structures in OLD_TSF
    cursor.execute("""
        SELECT 
            structure_id,
            structure_code,
            structure_name,
            structure_type
        FROM wb_structures 
        WHERE area_id = ?
        ORDER BY structure_code
    """, (area_id,))
    
    structures = cursor.fetchall()
    
    print("="*100)
    print("OLD_TSF AREA STRUCTURES")
    print("="*100)
    print(f"\nFound {len(structures)} structures:\n")
    
    for struct_id, code, name, struct_type in structures:
        print(f"  {code:20s} - {name:40s} ({struct_type})")
    
    # Find all self-loops in OLD_TSF
    cursor.execute("""
        SELECT 
            s.structure_id,
            s.structure_code,
            s.structure_name,
            fc.flow_type,
            fc.subcategory,
            fc.notes
        FROM wb_flow_connections fc
        JOIN wb_structures s ON fc.from_structure_id = s.structure_id
        WHERE s.area_id = ?
          AND fc.from_structure_id = fc.to_structure_id
        ORDER BY s.structure_code
    """, (area_id,))
    
    self_loops = cursor.fetchall()
    
    print("\n" + "="*100)
    print("OLD_TSF DAM SELF-LOOPS")
    print("="*100)
    print(f"\nFound {len(self_loops)} self-loops:\n")
    
    for struct_id, code, name, flow_type, subcategory, notes in self_loops:
        print(f"  {code:20s} - {name}")
        print(f"    Type: {flow_type} ({subcategory})")
        print(f"    Notes: {notes or 'N/A'}\n")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
