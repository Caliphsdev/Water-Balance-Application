import sqlite3

try:
    conn = sqlite3.connect('data/water_balance.db')
    cursor = conn.cursor()
    
    # Search for CPRWSD1_evap in flow connections
    cursor.execute("SELECT * FROM wb_flow_connections WHERE flow_code LIKE ?", 
                   ('%CPRWSD1%',))
    cprwsd1 = cursor.fetchall()
    print("CPRWSD1 references in wb_flow_connections:")
    print(f"  Found {len(cprwsd1)} records")
    for row in cprwsd1:
        print(f"    {row}")
    
    # Search for CPPWT_losses in flow connections
    cursor.execute("SELECT * FROM wb_flow_connections WHERE flow_code LIKE ?", 
                   ('%CPPWT%',))
    cppwt = cursor.fetchall()
    print("\nCPPWT references in wb_flow_connections:")
    print(f"  Found {len(cppwt)} records")
    for row in cppwt:
        print(f"    {row}")
    
    conn.close()
    print("\n✅ Database check complete")
except Exception as e:
    print(f"❌ Error: {e}")
