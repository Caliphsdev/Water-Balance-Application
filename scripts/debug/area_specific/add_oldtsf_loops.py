import sqlite3

try:
    conn = sqlite3.connect('data/water_balance.db')
    cursor = conn.cursor()
    
    # Get OLD_TSF area
    cursor.execute("SELECT area_id FROM wb_areas WHERE area_code = 'OLD_TSF'")
    area_id = cursor.fetchone()[0]
    
    # Get structure IDs for NT RWD and TRTD
    cursor.execute("""
        SELECT structure_id, structure_code 
        FROM wb_structures 
        WHERE area_id = ? AND structure_code IN ('OT_NT_RWD', 'OT_TRTD')
    """, (area_id,))
    
    structures = cursor.fetchall()
    struct_dict = {code: struct_id for struct_id, code in structures}
    
    if 'OT_NT_RWD' not in struct_dict or 'OT_TRTD' not in struct_dict:
        print("❌ Error: Could not find OT_NT_RWD or OT_TRTD structures")
        conn.close()
        exit(1)
    
    # Check for existing self-loops
    structures_to_add = []
    for code in ['OT_NT_RWD', 'OT_TRTD']:
        struct_id = struct_dict[code]
        cursor.execute("""
            SELECT connection_id FROM wb_flow_connections 
            WHERE from_structure_id = ? AND to_structure_id = ?
        """, (struct_id, struct_id))
        
        if not cursor.fetchone():
            structures_to_add.append((code, struct_id))
    
    if not structures_to_add:
        print("✅ All self-loops already exist for OT_NT_RWD and OT_TRTD")
        conn.close()
        exit(0)
    
    # Add missing self-loops
    for code, struct_id in structures_to_add:
        cursor.execute("""
            INSERT INTO wb_flow_connections (
                from_structure_id,
                to_structure_id,
                flow_type,
                subcategory,
                is_bidirectional,
                is_internal,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            struct_id,
            struct_id,
            'clean',
            'dam_return',
            0,
            1,
            f'{code} internal recirculation loop'
        ))
        print(f"✅ Added self-loop for {code}")
    
    conn.commit()
    
    # Verify
    cursor.execute("""
        SELECT s.structure_code, fc.connection_id
        FROM wb_flow_connections fc
        JOIN wb_structures s ON fc.from_structure_id = s.structure_id
        WHERE s.area_id = ?
          AND fc.from_structure_id = fc.to_structure_id
        ORDER BY s.structure_code
    """, (area_id,))
    
    all_loops = cursor.fetchall()
    print(f"\n{'='*80}")
    print(f"✅ OLD_TSF now has {len(all_loops)} self-loops:")
    for code, conn_id in all_loops:
        print(f"   {code}: Connection ID {conn_id}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
