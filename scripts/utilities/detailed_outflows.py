import re

# Read the template file
with open('OUTFLOW_CODES_TEMPLATE_CORRECTED.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Parse by area with detailed breakdown
areas_detail = {
    'MER_NORTH': [],
    'MER_PLANT': [],
    'MER_SOUTH': [],
    'OLD_TSF': [],
    'STOCKPILE': [],
    'UG2_NORTH': [],
    'UG2_PLANT': [],
    'UG2_SOUTH': []
}

current_area = None
lines = content.split('\n')

for line in lines:
    # Detect area headers
    if '📍 MER_NORTH' in line:
        current_area = 'MER_NORTH'
    elif '📍 MER_PLANT' in line:
        current_area = 'MER_PLANT'
    elif '📍 MER_SOUTH' in line:
        current_area = 'MER_SOUTH'
    elif '📍 OLD_TSF' in line:
        current_area = 'OLD_TSF'
    elif '📍 STOCKPILE' in line:
        current_area = 'STOCKPILE'
    elif '📍 UG2_NORTH' in line:
        current_area = 'UG2_NORTH'
    elif '📍 UG2_PLANT' in line:
        current_area = 'UG2_PLANT'
    elif '📍 UG2_SOUTH' in line:
        current_area = 'UG2_SOUTH'
    
    # Extract values for current area
    if current_area and '=' in line and 'm³' in line:
        value_match = re.search(r'=\s*([\d\s,]+)\s*m³', line)
        if value_match:
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
                # Extract code and category
                code_match = re.search(r'(\w+(?:_\w+)*)\s+(?:\u2192|\u2194)?\s*(?:\w+(?:_\w+)*)?\s*\((\w+)', line)
                if code_match:
                    code = code_match.group(1)
                    category = code_match.group(2)
                else:
                    # Try simpler pattern
                    code_match = re.search(r'(\w+(?:_\w+)*)', line)
                    code = code_match.group(1) if code_match else 'UNKNOWN'
                    category = 'unknown'
                
                areas_detail[current_area].append({
                    'code': code,
                    'category': category,
                    'value': value,
                    'line': line.strip()
                })
            except:
                continue

# Print detailed breakdown
print("="*100)
print("DETAILED OUTFLOW BREAKDOWN BY AREA")
print("="*100)

grand_total = 0
for area in ['MER_NORTH', 'MER_PLANT', 'MER_SOUTH', 'OLD_TSF', 'STOCKPILE', 'UG2_NORTH', 'UG2_PLANT', 'UG2_SOUTH']:
    items = areas_detail[area]
    area_total = sum(item['value'] for item in items)
    grand_total += area_total
    
    print(f"\n{'='*100}")
    print(f"📍 {area}")
    print(f"{'='*100}")
    
    # Group by category
    categories = {}
    for item in items:
        cat = item['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # Print by category
    for cat, cat_items in sorted(categories.items()):
        cat_total = sum(item['value'] for item in cat_items)
        print(f"\n  {cat.upper()}: {cat_total:>15,.0f} m³")
        for item in cat_items:
            print(f"    {item['code']:30s} = {item['value']:>12,.0f} m³")
    
    print(f"\n  {'─'*94}")
    print(f"  AREA TOTAL: {area_total:>15,.0f} m³")

print(f"\n{'='*100}")
print(f"📊 GRAND TOTAL (ALL AREAS): {grand_total:>15,.0f} m³")
print(f"{'='*100}")

# Summary by category across all areas
print(f"\n{'='*100}")
print("SUMMARY BY CATEGORY (ALL AREAS)")
print(f"{'='*100}")

all_categories = {}
for area, items in areas_detail.items():
    for item in items:
        cat = item['category']
        if cat not in all_categories:
            all_categories[cat] = 0
        all_categories[cat] += item['value']

for cat, total in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat:20s}: {total:>15,.0f} m³")
