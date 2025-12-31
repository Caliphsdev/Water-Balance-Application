import sqlite3

try:
    conn = sqlite3.connect('data/water_balance.db')
    cursor = conn.cursor()
    
    # Get UG2N_NDCDG structure_id
    cursor.execute("SELECT structure_id FROM wb_structures WHERE structure_code = 'UG2N_NDCDG'")
    result = cursor.fetchone()
    
    if not result:
        print("❌ Error: UG2N_NDCDG structure not found in database")
        conn.close()
        exit(1)
    
    structure_id = result[0]
    print(f"✅ Found UG2N_NDCDG structure with ID: {structure_id}")
    
    # Check if self-loop already exists
    cursor.execute("""
        SELECT connection_id FROM wb_flow_connections 
        WHERE from_structure_id = ? AND to_structure_id = ?
    """, (structure_id, structure_id))
    
    existing = cursor.fetchone()
    
    if existing:
        print(f"⚠️  Self-loop already exists with connection_id: {existing[0]}")
        conn.close()
        exit(0)
    
    # Insert self-loop
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
        structure_id,
        structure_id,
        'clean',
        'dam_return',
        0,
        1,
        'UG2N NDCD 1-2 & NDSWD 1 Group dam return loop (internal recirculation)'
    ))
    
    conn.commit()
    
    # Verify insertion
    cursor.execute("""
        SELECT connection_id, flow_type, subcategory, notes
        FROM wb_flow_connections 
        WHERE from_structure_id = ? AND to_structure_id = ?
    """, (structure_id, structure_id))
    
    new_loop = cursor.fetchone()
    
    if new_loop:
        print(f"\n✅ Successfully added UG2N_NDCDG self-loop!")
        print(f"   Connection ID: {new_loop[0]}")
        print(f"   Flow Type: {new_loop[1]}")
        print(f"   Subcategory: {new_loop[2]}")
        print(f"   Notes: {new_loop[3]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
