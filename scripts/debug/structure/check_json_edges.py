"""
Check actual JSON edges count and detailed flow analysis.
"""
import json

with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)

edges = diagram.get('edges', [])
print(f'Total edges in JSON: {len(edges)}')
print()

# Group by from_id
from collections import defaultdict
by_source = defaultdict(int)
for edge in edges:
    from_id = edge.get('from')
    by_source[from_id] += 1

# Show top 10 sources with most flows
print('Top nodes by outflow count:')
for source in sorted(by_source.keys(), key=lambda x: by_source[x], reverse=True)[:20]:
    print(f'  {source}: {by_source[source]} flows')
