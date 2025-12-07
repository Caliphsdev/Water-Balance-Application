import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check outflows for each Stockpile structure
stockpile_structures = ['STP_STOCK', 'STP_SPCD1', 'STP_OFF', 'STP_SEPTIC']

for struct_code in stockpile_structures:
    print(f"\n=== OUTFLOWS FOR {struct_code} ===")
    cursor.execute('''
        SELECT od.destination_code, od.destination_type, od.destination_name
        FROM wb_outflow_destinations od
        JOIN wb_structures s ON od.source_structure_id = s.structure_id
        WHERE s.structure_code = ?
        ORDER BY od.destination_type
    ''', (struct_code,))
    outflows = cursor.fetchall()
    print(f"Outflows found: {len(outflows)}")
    for row in outflows:
        print(f"  {row['destination_code']:30} ({row['destination_type']:15}) - {row['destination_name']}")

conn.close()
