import re

# Read the template file
with open('OUTFLOW_CODES_TEMPLATE_CORRECTED.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match lines with numeric values (not _____)
pattern = r'=\s*([\d\s,]+)\s*m³'

# Extract all numeric values
matches = re.findall(pattern, content)

# Clean and convert to floats
values = []
for match in matches:
    # Remove spaces and commas
    cleaned = match.replace(' ', '').replace(',', '')
    try:
        value = float(cleaned)
        values.append(value)
    except ValueError:
        continue

# Calculate totals by category
evaporation_total = 0
ug_return_total = 0
proc_losses_total = 0
consumption_total = 0
dust_suppress_total = 0
spill_total = 0
product_bound_total = 0
septic_total = 0
irrigation_total = 0
seepage_total = 0
interstitial_total = 0

# Re-parse with categories
lines = content.split('\n')
for line in lines:
    if '=' in line and 'm³' in line and '_____' not in line:
        # Extract value
        value_match = re.search(r'=\s*([\d\s,]+)\s*m³', line)
        if value_match:
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
            except:
                continue
            
            # Categorize
            if 'evaporation' in line or '_evap' in line:
                evaporation_total += value
            elif 'ug_return' in line:
                ug_return_total += value
            elif 'proc_losses' in line or '_losses' in line:
                proc_losses_total += value
            elif 'consumption' in line:
                consumption_total += value
            elif 'dust_suppr' in line or 'dust_suppress' in line:
                dust_suppress_total += value
            elif 'spill' in line:
                spill_total += value
            elif 'product_bnd' in line or 'product' in line:
                product_bound_total += value
            elif 'septic' in line:
                septic_total += value
            elif 'irrigation' in line:
                irrigation_total += value
            elif 'seepage' in line:
                seepage_total += value
            elif 'interstitial' in line:
                interstitial_total += value

# Calculate grand total
grand_total = sum(values)

# Print results
print("="*80)
print("OUTFLOW SUMMARY - BY CATEGORY")
print("="*80)
print(f"\n💧 EVAPORATION (Auto-calculated):        {evaporation_total:>15,.0f} m³")
print(f"⬇️  UNDERGROUND RETURN:                  {ug_return_total:>15,.0f} m³")
print(f"🏭 PROCESS LOSSES:                       {proc_losses_total:>15,.0f} m³")
print(f"🏭 PRODUCT BOUND WATER:                  {product_bound_total:>15,.0f} m³")
print(f"💦 CONSUMPTION:                          {consumption_total:>15,.0f} m³")
print(f"💦 DUST SUPPRESSION:                     {dust_suppress_total:>15,.0f} m³")
print(f"💧 SPILLAGE:                             {spill_total:>15,.0f} m³")
print(f"🚰 SEPTIC TANKS:                         {septic_total:>15,.0f} m³")
print(f"♻️  IRRIGATION (Internal Recirc):        {irrigation_total:>15,.0f} m³")
print(f"💧 SEEPAGE:                              {seepage_total:>15,.0f} m³")
print(f"💧 INTERSTITIAL STORAGE:                 {interstitial_total:>15,.0f} m³")

print("\n" + "="*80)
print(f"📊 GRAND TOTAL (ALL OUTFLOWS):          {grand_total:>15,.0f} m³")
print("="*80)

# Breakdown by area
print("\n" + "="*80)
print("BREAKDOWN BY AREA")
print("="*80)

areas = {
    'MER_NORTH': 0,
    'MER_PLANT': 0,
    'MER_SOUTH': 0,
    'OLD_TSF': 0,
    'STOCKPILE': 0,
    'UG2_NORTH': 0,
    'UG2_PLANT': 0,
    'UG2_SOUTH': 0
}

current_area = None
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
    if current_area and '=' in line and 'm³' in line and '_____' not in line:
        value_match = re.search(r'=\s*([\d\s,]+)\s*m³', line)
        if value_match:
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
                areas[current_area] += value
            except:
                continue

for area, total in sorted(areas.items()):
    print(f"{area:20s}: {total:>15,.0f} m³")

print("\n✅ Calculation complete!")
print(f"📝 Total values counted: {len(values)}")
