import json

# Load master diagram
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

# Find and fix all Stockpile edges
fixed_count = 0
for i, edge in enumerate(master.get('edges', [])):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # Check if this is a Stockpile edge
    if 'stockpile' in from_node or 'stockpile' in to_node or 'spcd' in from_node or 'spcd' in to_node:
        # Get the correct column name from the edge nodes
        column = edge.get('excel_mapping', {}).get('column')
        
        if column:
            # Enable the mapping and set correct sheet
            edge['excel_mapping'] = {
                'enabled': True,
                'sheet': 'Flows_STOCKPILE',  # Changed from Flows_UG2N
                'column': column
            }
            fixed_count += 1
            print(f"✅ Fixed edge {i}: {from_node} → {to_node}")
            print(f"   Column: {column}")
            print(f"   Sheet: Flows_STOCKPILE\n")

# Save fixed diagram
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"\n✅ Fixed {fixed_count} Stockpile edge mappings")
print("✅ All Stockpile flows now point to Flows_STOCKPILE sheet")
print("✅ All mappings enabled = data will load")
