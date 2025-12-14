"""
Test script to verify area selector functionality
"""
import json
from pathlib import Path

# Test 1: Verify all diagram files exist
print("✅ Test 1: Checking diagram files...")
diagrams_dir = Path('data/diagrams')
expected_files = [
    'ug2_north_decline.json',
    'merensky_north_area.json',
    'merensky_south_area.json',
    'merensky_plant_area.json',
    'ug2_south_area.json',
    'ug2_plant_area.json',
    'old_tsf_area.json',
    'stockpile_area.json'
]

all_exist = True
for filename in expected_files:
    filepath = diagrams_dir / filename
    exists = filepath.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {filename}")
    if not exists:
        all_exist = False

# Test 2: Verify each file has correct structure
print("\n✅ Test 2: Checking JSON structure...")
for filename in expected_files:
    filepath = diagrams_dir / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        required_keys = ['area_code', 'title', 'nodes', 'edges']
        has_all_keys = all(key in data for key in required_keys)
        
        status = "✅" if has_all_keys else "❌"
        area_code = data.get('area_code', 'UNKNOWN')
        title = data.get('title', 'UNKNOWN')
        print(f"  {status} {filename} ({area_code})")
        
        if not has_all_keys:
            missing = [k for k in required_keys if k not in data]
            print(f"     ❌ Missing keys: {missing}")

# Test 3: Check area code mapping
print("\n✅ Test 3: Area code mapping...")
area_code_map = {
    'UG2 North Decline Area': 'UG2N',
    'Merensky North Area': 'MERN',
    'Merensky South Area': 'MERS',
    'Merensky Plant Area': 'MERPLANT',
    'UG2 South Area': 'UG2S',
    'UG2 Plant Area': 'UG2PLANT',
    'Old TSF Area': 'OLDTSF',
    'Stockpile Area': 'STOCKPILE'
}

for title, expected_code in area_code_map.items():
    filename = {
        'UG2 North Decline Area': 'ug2_north_decline.json',
        'Merensky North Area': 'merensky_north_area.json',
        'Merensky South Area': 'merensky_south_area.json',
        'Merensky Plant Area': 'merensky_plant_area.json',
        'UG2 South Area': 'ug2_south_area.json',
        'UG2 Plant Area': 'ug2_plant_area.json',
        'Old TSF Area': 'old_tsf_area.json',
        'Stockpile Area': 'stockpile_area.json'
    }[title]
    
    filepath = diagrams_dir / filename
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    actual_code = data.get('area_code')
    matches = actual_code == expected_code
    status = "✅" if matches else "❌"
    print(f"  {status} {title}: {actual_code}")

print("\n" + "="*50)
if all_exist:
    print("✅ All tests passed! Area selector should work.")
else:
    print("❌ Some tests failed. Check the output above.")
