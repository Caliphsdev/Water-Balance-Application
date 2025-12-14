import json

m = json.load(open('data/diagrams/ug2_north_decline.json'))
edges = m.get('edges', [])

# Count Stockpile edges
spcd = [e for i, e in enumerate(edges) if 'spcd' in e.get('from', '').lower() or 'spcd' in e.get('to', '').lower() or 'stockpile' in e.get('from', '').lower() or 'stockpile' in e.get('to', '').lower()]

print("STOCKPILE MAPPINGS - VERIFICATION")
print("=" * 50)
print(f"Total Stockpile edges: {len(spcd)}")

enabled_count = sum(1 for e in spcd if e.get('excel_mapping', {}).get('enabled'))
print(f"Enabled mappings: {enabled_count}")

# Show first few
print(f"\nFirst 5 mappings:")
for i, edge in enumerate(spcd[:5]):
    mapping = edge.get('excel_mapping', {})
    print(f"\n  Edge {i}:")
    print(f"    From: {edge.get('from')}")
    print(f"    To: {edge.get('to')}")
    print(f"    Sheet: {mapping.get('sheet')}")
    print(f"    Column: {mapping.get('column')}")
    print(f"    Enabled: {mapping.get('enabled')}")

print("\n" + "=" * 50)
if enabled_count == len(spcd):
    print("✅ ALL STOCKPILE MAPPINGS ENABLED")
    print("✅ Data will load when you press 'Load from Excel'")
else:
    print(f"⚠️  {len(spcd) - enabled_count} mappings still disabled")
