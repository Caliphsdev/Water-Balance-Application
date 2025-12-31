"""Check if JSON edges have excel_mapping configured."""
import json
from pathlib import Path

json_file = Path('data/diagrams/ug2_north_decline.json')
with open(json_file, 'r') as f:
    data = json.load(f)

edges = data.get('edges', [])
print(f'📊 Total edges: {len(edges)}\n')

# Check how many have excel_mapping
mapped_count = 0
enabled_count = 0

for i, edge in enumerate(edges[:5]):  # Check first 5
    excel_mapping = edge.get('excel_mapping', {})
    has_mapping = bool(excel_mapping)
    is_enabled = excel_mapping.get('enabled', False) if excel_mapping else False
    
    if has_mapping:
        mapped_count += 1
    if is_enabled:
        enabled_count += 1
    
    print(f'Edge {i+1}: {edge.get("from")} → {edge.get("to")}')
    print(f'  Has excel_mapping: {has_mapping}')
    print(f'  Enabled: {is_enabled}')
    if excel_mapping:
        print(f'  Column: {excel_mapping.get("column", "N/A")}')
    print()

print(f'\n✅ Summary: {mapped_count}/5 have mapping, {enabled_count}/5 enabled')
print(f'\n⚠️  If enabled_count is 0, edges need Excel mapping configuration!')
