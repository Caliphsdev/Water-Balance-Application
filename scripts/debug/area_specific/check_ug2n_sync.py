#!/usr/bin/env python
import json

with open('data/diagrams/ug2_north_decline.json') as f:
    data = json.load(f)

ug2n_flows = [e for e in data['edges'] if e.get('excel_mapping', {}).get('sheet') == 'Flows_UG2N']
print(f"Total UG2N flows: {len(ug2n_flows)}\n")

# Check specific ones we care about
target_flows = ['rainfall', 'ndcd', 'softening', 'trp_clinic', 'offices', 'sewage']
for target in target_flows:
    flows = [e for e in ug2n_flows if target in e.get('from', '').lower()]
    print(f"\nFlows FROM {target}:")
    for e in flows[:3]:
        col = e.get('excel_mapping', {}).get('column', 'NOT SET')
        print(f"  {e.get('from')} -> {e.get('to')}: {col}")
