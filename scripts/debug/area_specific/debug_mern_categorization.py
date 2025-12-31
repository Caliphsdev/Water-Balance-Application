"""
Debug exact categorization: trace each flow assignment.
"""
import json

with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)

area_definitions = {
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

def find_area_for_node(node_id):
    """Find which area a node belongs to."""
    if not node_id:
        return None
    
    node_lower = node_id.lower()
    
    # Check each area's patterns
    for area, patterns in area_definitions.items():
        for pattern in patterns:
            if pattern in node_lower:
                return area
    
    return None

# Check which merensky flows are being categorized incorrectly
edges = diagram.get('edges', [])
mern_expected = 14
mern_found = 0

print("Merensky flows categorization:")
print("=" * 100)

for edge in edges:
    from_id = edge.get('from')
    to_id = edge.get('to')
    
    # Check if this should be a MERN flow
    if any(pat in str(from_id).lower() + str(to_id).lower() for pat in ['merensky', '_merensky']):
        # Now check categorization
        source_area = find_area_for_node(from_id)
        dest_area = find_area_for_node(to_id)
        actual_area = source_area if source_area else dest_area
        
        status = '✅' if actual_area == 'MERN' else '❌'
        print(f"{status} {from_id} → {to_id}")
        print(f"   Source area: {source_area}, Dest area: {dest_area}, Assigned: {actual_area}")
        
        if actual_area == 'MERN':
            mern_found += 1

print(f"\n📊 Expected MERN flows: {mern_expected}")
print(f"📊 Found MERN flows: {mern_found}")
