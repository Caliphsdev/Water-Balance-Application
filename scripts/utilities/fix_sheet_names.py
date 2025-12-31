import json

# Load master diagram
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Fix sheet name mappings
replacements = {
    'Flows_MERPLANT': 'Flows_MERP',
    'Flows_UG2PLANT': 'Flows_UG2P'
}

updated = 0

for edge in edges:
    mapping = edge.get('excel_mapping', {})
    current_sheet = mapping.get('sheet', '')
    
    if current_sheet in replacements:
        edge['excel_mapping']['sheet'] = replacements[current_sheet]
        updated += 1
        if updated <= 5:  # Print first 5
            print(f"✅ {edge.get('from')[:20]:20} → {edge.get('to')[:20]:20}")
            print(f"   Changed: {current_sheet} → {replacements[current_sheet]}")

# Save
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"\n{'='*70}")
print(f"Fixed {updated} sheet name mappings")
print(f"{'='*70}")
