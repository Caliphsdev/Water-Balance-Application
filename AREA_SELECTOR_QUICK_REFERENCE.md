"""
Quick Reference: How to Use the Area Selector
"""

AREA_SELECTOR_LOCATIONS = {
    'UI Location': 'Top of Flow Diagram Dashboard (below title)',
    'Appearance': 'Dropdown labeled "📍 Select Area:" with "📂 Load Area" button',
    'Default Area': 'UG2 North Decline Area'
}

AVAILABLE_AREAS = [
    '🔵 UG2 North Decline Area (UG2N)',
    '🟢 Merensky North Area (MERN)',
    '🟡 Merensky South Area (MERS)',
    '🟠 Merensky Plant Area (MERPLANT)',
    '🔴 UG2 South Area (UG2S)',
    '🟣 UG2 Plant Area (UG2PLANT)',
    '⚫ Old TSF Area (OLDTSF)',
    '⚪ Stockpile Area (STOCKPILE)'  # ✅ NOW FIXED!
]

QUICK_START = """
1. Open Flow Diagram module
2. Look for area dropdown at top (📍 Select Area:)
3. Click dropdown to see all 8 areas
4. Select desired area (e.g., "Stockpile Area")
5. Click "📂 Load Area" button
6. Diagram loads for that area
7. Use existing tools to draw, edit, add flows
8. Click "🔄 Load from Excel" to populate volumes (if data exists)
9. Click "💾 Save" to save diagram
10. Switch to another area anytime using dropdown
"""

AREA_MAPPING = {
    'UI Display Name': 'Excel Sheet Name': 'Area Code': 'JSON File',
    'UG2 North Decline Area': 'Flows_UG2N': 'UG2N': 'ug2_north_decline.json',
    'Merensky North Area': 'Flows_MERN': 'MERN': 'merensky_north_area.json',
    'Merensky South Area': 'Flows_MERS': 'MERS': 'merensky_south_area.json',
    'Merensky Plant Area': 'Flows_MERPLANT': 'MERPLANT': 'merensky_plant_area.json',
    'UG2 South Area': 'Flows_UG2S': 'UG2S': 'ug2_south_area.json',
    'UG2 Plant Area': 'Flows_UG2PLANT': 'UG2PLANT': 'ug2_plant_area.json',
    'Old TSF Area': 'Flows_OLDTSF': 'OLDTSF': 'old_tsf_area.json',
    'Stockpile Area': 'Flows_STOCKPILE': 'STOCKPILE': 'stockpile_area.json'
}

print("=" * 60)
print("AREA SELECTOR - QUICK REFERENCE")
print("=" * 60)
print()
print("✅ AVAILABLE AREAS:")
for area in AVAILABLE_AREAS:
    print(f"   {area}")
print()
print("✅ HOW TO USE:")
print(QUICK_START)
print()
print("=" * 60)
