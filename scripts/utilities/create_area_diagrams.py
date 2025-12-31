import json
from pathlib import Path

# Load the working UG2N diagram as a template
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    ug2n_template = json.load(f)

# Define area templates with appropriate titles and area codes
areas = [
    {
        'filename': 'merensky_north_area.json',
        'title': 'Merensky North Area',
        'area_code': 'MERN'
    },
    {
        'filename': 'merensky_south_area.json',
        'title': 'Merensky South Area',
        'area_code': 'MERS'
    },
    {
        'filename': 'merensky_plant_area.json',
        'title': 'Merensky Plant Area',
        'area_code': 'MERPLANT'
    },
    {
        'filename': 'ug2_south_area.json',
        'title': 'UG2 South Area',
        'area_code': 'UG2S'
    },
    {
        'filename': 'ug2_plant_area.json',
        'title': 'UG2 Plant Area',
        'area_code': 'UG2PLANT'
    },
    {
        'filename': 'old_tsf_area.json',
        'title': 'Old TSF Area',
        'area_code': 'OLDTSF'
    },
    {
        'filename': 'stockpile_area.json',
        'title': 'Stockpile Area',
        'area_code': 'STOCKPILE'
    }
]

# Create minimal diagram files for each area
for area in areas:
    # Create a basic structure with just essential fields
    diagram = {
        'area_code': area['area_code'],
        'title': area['title'],
        'width': ug2n_template.get('width', 1400),
        'height': ug2n_template.get('height', 900),
        'nodes': [],  # Start with empty nodes (user will add them)
        'edges': [],  # Start with empty edges (user will add them)
        'zone_bg': ug2n_template.get('zone_bg', [])  # Copy zone backgrounds if they exist
    }
    
    # Copy zone_bg data if it exists for this area
    if 'zone_bg' in ug2n_template and isinstance(ug2n_template['zone_bg'], list):
        diagram['zone_bg'] = ug2n_template['zone_bg']
    
    filepath = Path('data/diagrams') / area['filename']
    with open(filepath, 'w') as f:
        json.dump(diagram, f, indent=2)
    
    print(f"✅ Created: {area['filename']} ({area['title']})")

print(f"\n✅ Created {len(areas)} diagram files")
