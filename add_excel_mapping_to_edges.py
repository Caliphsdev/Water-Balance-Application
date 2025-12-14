"""
Add excel_mapping configuration to all edges in the UG2N diagram.
Maps edge IDs to Excel column names automatically.
"""
import json
from pathlib import Path

json_file = Path('data/diagrams/ug2_north_decline.json')

# Read the diagram
with open(json_file, 'r') as f:
    data = json.load(f)

edges = data.get('edges', [])
print(f'📊 Processing {len(edges)} edges...\n')

updated_count = 0
skipped_count = 0

for edge in edges:
    from_id = edge.get('from', '')
    to_id = edge.get('to', '')
    
    # Skip if already has mapping
    if edge.get('excel_mapping', {}).get('enabled'):
        skipped_count += 1
        continue
    
    # Generate column name from edge IDs
    # Format: from__TO__to (matching Excel column format)
    column_name = f"{from_id}__TO__{to_id}"
    
    # Add excel_mapping
    edge['excel_mapping'] = {
        'enabled': True,
        'column': column_name,
        'sheet': 'Flows_UG2N'
    }
    
    updated_count += 1
    
    if updated_count <= 5:
        print(f'✓ {from_id} → {to_id}')
        print(f'  Column: {column_name}\n')

print(f'\n✅ Updated: {updated_count} edges')
print(f'⏭️  Skipped: {skipped_count} edges (already mapped)')

# Save back to JSON
with open(json_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f'\n💾 Saved to: {json_file}')
print(f'\n📋 Next steps:')
print(f'   1. Restart the app')
print(f'   2. Go to Flow Diagram')
print(f'   3. Click "🔄 Load from Excel"')
print(f'   4. Values should update!')
