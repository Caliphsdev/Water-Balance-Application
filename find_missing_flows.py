"""
Find flows in JSON that aren't being categorized into any area.
"""
from pathlib import Path
import json

# Load JSON diagram
with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)

# All flows in JSON
all_flows = [(e.get('from'), e.get('to')) for e in diagram.get('edges', [])]

# Area patterns (current categorization)
area_patterns = {
    'UG2N': ['rainfall', 'ndcd', 'bh_ndgwa', 'softening', 'reservoir', 'offices', 
             'guest_house', 'septic', 'sewage', 'north_decline', 'north_shaft', 
             'losses', 'losses2', 'consumption', 'consumption2', 'evaporation',
             'dust_suppression', 'spill', 'junction_127', 'junction_128'],
    'UG2S': ['ug2s_'],
    'UG2P': ['ug2plant_', 'cprwsd'],
    'MERN': ['rainfall_merensky', 'ndcd_merensky', 'bh_mcgwa', 'softening_merensky', 
             'offices_merensky', 'merensky_north', 'evaporation_merensky', 'dust_suppression_merensky',
             'spill_merensky', 'consumption_merensky', 'losses_merensky', 'junction_128'],
    'MERP': ['merplant_', 'mprwsd'],
    'MERS': ['mers_'],
    'OLDTSF': ['oldtsf_', 'nt_rwd', 'new_tsf', 'trtd'],
    'STOCKPILE': ['stockpile_', 'spcd1'],
}

# Find which flows belong to which area
uncategorized = []

for from_id, to_id in all_flows:
    found_area = None
    for area, patterns in area_patterns.items():
        for pattern in patterns:
            if (from_id and pattern in from_id) or (to_id and pattern in to_id):
                found_area = area
                break
        if found_area:
            break
    
    if not found_area:
        uncategorized.append((from_id, to_id))

print(f'📊 UNCATEGORIZED FLOWS')
print(f'=' * 100)
print(f'Total flows in JSON: {len(all_flows)}')
print(f'Uncategorized flows: {len(uncategorized)}')
print()

# Group uncategorized by starting node
from collections import defaultdict
by_source = defaultdict(list)
for from_id, to_id in uncategorized:
    by_source[from_id].append(to_id)

print('Uncategorized flows by source node:')
print()
for source in sorted(by_source.keys()):
    dests = by_source[source]
    print(f'  {source} ({len(dests)} flows):')
    for dest in sorted(dests)[:5]:
        print(f'    → {dest}')
    if len(dests) > 5:
        print(f'    ... and {len(dests) - 5} more')
    print()
