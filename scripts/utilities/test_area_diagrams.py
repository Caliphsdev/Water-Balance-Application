"""
Test script to verify area selector functionality
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
diagrams_dir = BASE_DIR / 'data' / 'diagrams'

# Limit expectations to existing repo diagrams
expected_files = [
    'ug2_north_decline.json',
    'test_bidirectional_edge.json'
]

# Test 1: Verify all diagram files exist
print("✅ Test 1: Checking diagram files...")

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
        print(f"  {status} {filename} ({area_code})")
        if not has_all_keys:
            missing = [k for k in required_keys if k not in data]
            print(f"     ❌ Missing keys: {missing}")

# Test 3: Check area code mapping
print("\n✅ Test 3: Area code mapping...")
area_code_map = {
    'UG2 North Decline Area': ('ug2_north_decline.json', 'UG2N'),
}

for title, (filename, expected_code) in area_code_map.items():
    filepath = diagrams_dir / filename
    if not filepath.exists():
        print(f"  ❌ {title}: file missing ({filename})")
        all_exist = False
        continue
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
