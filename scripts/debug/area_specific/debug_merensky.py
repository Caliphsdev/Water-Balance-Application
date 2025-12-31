"""
Analyze the categorization issue - check why MERN and other areas have wrong counts.
"""
import json

with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)

edges = diagram.get('edges', [])

# Find all nodes containing 'merensky' or 'ndcd_merensky'
merensky_flows = []
for edge in edges:
    from_id = edge.get('from')
    to_id = edge.get('to')
    
    if any(pat in str(from_id).lower() + str(to_id).lower() for pat in ['merensky', 'ndcd_merensky']):
        merensky_flows.append((from_id, to_id))

print(f"Flows containing 'merensky' patterns: {len(merensky_flows)}")
print("\nAll merensky-related flows:")
for from_id, to_id in sorted(merensky_flows):
    print(f"  {from_id} → {to_id}")
