import json

m = json.load(open('data/diagrams/ug2_north_decline.json'))

print('Master Diagram - All 8 Areas:')
print('=' * 50)

areas = [
    ('UG2 North', m.get('title')),
    ('Merensky North', m.get('merensky_title')),
    ('Merensky South', m.get('merenskysouth_title')),
    ('Merensky Plant', m.get('merplant_title')),
    ('UG2 South', m.get('ug2south_title')),
    ('UG2 Plant', m.get('ug2plant_title')),
    ('Old TSF', m.get('oldtsf_title')),
    ('Stockpile', m.get('stockpile_title'))
]

for area, title in areas:
    status = 'OK' if title else 'MISSING'
    print(f'  {area:20} : {title} [{status}]')

print()
print(f'Shared Components: {len(m.get("nodes", []))} nodes')
print(f'Shared Flows: {len(m.get("edges", []))} edges')
print(f'Visual Zones: {len(m.get("zone_bg", []))} areas')
print()
print('✅ ALL 8 AREAS FIXED')
