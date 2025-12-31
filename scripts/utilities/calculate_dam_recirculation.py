import re

# Read the template file
with open('DAM_RECIRCULATION_TEMPLATE.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all numeric values (not placeholders)
pattern = r'=\s*([-\d\s,]+)\s*m³'
matches = re.findall(pattern, content)

# Parse and sum values
values = []
areas_data = {}
current_area = None

lines = content.split('\n')
for line in lines:
    # Detect area headers
    if '📍 MER_NORTH' in line:
        current_area = 'MER_NORTH'
        areas_data[current_area] = []
    elif '📍 MER_PLANT' in line:
        current_area = 'MER_PLANT'
        areas_data[current_area] = []
    elif '📍 MER_SOUTH' in line:
        current_area = 'MER_SOUTH'
        areas_data[current_area] = []
    elif '📍 OLD_TSF' in line:
        current_area = 'OLD_TSF'
        areas_data[current_area] = []
    elif '📍 STOCKPILE' in line:
        current_area = 'STOCKPILE'
        areas_data[current_area] = []
    elif '📍 UG2_NORTH' in line:
        current_area = 'UG2_NORTH'
        areas_data[current_area] = []
    elif '📍 UG2_PLANT' in line:
        current_area = 'UG2_PLANT'
        areas_data[current_area] = []
    elif '📍 UG2_SOUTH' in line:
        current_area = 'UG2_SOUTH'
        areas_data[current_area] = []
    
    # Extract values
    if current_area and '↻' in line and '=' in line and 'm³' in line and '_____' not in line:
        # Extract code and value
        code_match = re.search(r'(\w+(?:_\w+)*)\s*↻', line)
        value_match = re.search(r'=\s*([-\d\s,]+)\s*m³', line)
        
        if code_match and value_match:
            code = code_match.group(1)
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
                values.append(value)
                areas_data[current_area].append({
                    'code': code,
                    'value': value,
                    'line': line.strip()
                })
            except:
                continue

# Calculate totals
grand_total = sum(values)

# Print results
print("="*100)
print("DAM RECIRCULATION SUMMARY - BY AREA")
print("="*100)

for area in ['MER_NORTH', 'MER_PLANT', 'MER_SOUTH', 'OLD_TSF', 'STOCKPILE', 'UG2_NORTH', 'UG2_PLANT', 'UG2_SOUTH']:
    if area in areas_data and areas_data[area]:
        area_total = sum(item['value'] for item in areas_data[area])
        print(f"\n📍 {area:20s}: {area_total:>15,.0f} m³")
        for item in areas_data[area]:
            print(f"    {item['code']:30s} = {item['value']:>12,.0f} m³")

print("\n" + "="*100)
print(f"📊 GRAND TOTAL (DAM RECIRCULATION): {grand_total:>15,.0f} m³")
print("="*100)

print(f"\n✅ Calculation complete!")
print(f"📝 Total dam self-loops counted: {len(values)}")
print(f"\n⚠️  NOTE: These are INTERNAL flows that loop within dams.")
print(f"   They do NOT count as area inflows/outflows.")
print(f"   Net effect on water balance = ZERO")
