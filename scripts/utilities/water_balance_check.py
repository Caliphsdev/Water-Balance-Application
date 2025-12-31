import re

# Read both templates
with open('INFLOW_CODES_TEMPLATE.txt', 'r', encoding='utf-8') as f:
    inflow_content = f.read()

with open('OUTFLOW_CODES_TEMPLATE_CORRECTED.txt', 'r', encoding='utf-8') as f:
    outflow_content = f.read()

with open('DAM_RECIRCULATION_TEMPLATE.txt', 'r', encoding='utf-8') as f:
    recirculation_content = f.read()

# Extract all numeric values
pattern = r'=\s*([-\d\s,]+)\s*m³'

# Calculate inflows
inflow_values = []
lines = inflow_content.split('\n')
for line in lines:
    if '=' in line and 'm³' in line and '_____' not in line:
        value_match = re.search(pattern, line)
        if value_match:
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
                inflow_values.append(value)
            except:
                continue

# Calculate outflows
outflow_values = []
lines = outflow_content.split('\n')
for line in lines:
    if '=' in line and 'm³' in line and '_____' not in line:
        value_match = re.search(pattern, line)
        if value_match:
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
                outflow_values.append(value)
            except:
                continue

# Calculate dam recirculation
recirculation_values = []
lines = recirculation_content.split('\n')
for line in lines:
    if '↻' in line and '=' in line and 'm³' in line and '_____' not in line:
        value_match = re.search(pattern, line)
        if value_match:
            value_str = value_match.group(1).replace(' ', '').replace(',', '')
            try:
                value = float(value_str)
                recirculation_values.append(value)
            except:
                continue

# Calculate totals
total_inflows = sum(inflow_values)
total_outflows = sum(outflow_values)
total_recirculation = sum(recirculation_values)

# Water Balance Formula
# Balance Error % = (Total Inflows - Dam Recirculation - Total Outflows) / Total Inflows × 100
numerator = total_inflows - total_recirculation - total_outflows
balance_error_pct = (numerator / total_inflows) * 100 if total_inflows != 0 else 0

# Print results
print("="*100)
print("WATER BALANCE CLOSURE CHECK")
print("="*100)

print(f"\n📊 BALANCE COMPONENTS:")
print(f"{'─'*100}")
print(f"  Total INFLOWS:                   {total_inflows:>20,.0f} m³")
print(f"  Total DAM RECIRCULATION:         {total_recirculation:>20,.0f} m³")
print(f"  Total OUTFLOWS:                  {total_outflows:>20,.0f} m³")

print(f"\n{'─'*100}")
print(f"  Inflows - Recirculation - Outflows:")
print(f"  {total_inflows:,.0f} - {total_recirculation:,.0f} - {total_outflows:,.0f}")
print(f"  = {numerator:,.0f} m³")

print(f"\n{'='*100}")
print(f"BALANCE ERROR % = ({numerator:,.0f} / {total_inflows:,.0f}) × 100")
print(f"BALANCE ERROR % = {balance_error_pct:.2f}%")
print(f"{'='*100}")

# Interpretation
print(f"\n📋 INTERPRETATION:")
print(f"{'─'*100}")

if abs(balance_error_pct) < 1:
    print(f"✅ EXCELLENT BALANCE: {balance_error_pct:.2f}% (±1%)")
    print(f"   Water balance is well-closed. Measurement and calculations are reliable.")
elif abs(balance_error_pct) < 5:
    print(f"⚠️  GOOD BALANCE: {balance_error_pct:.2f}% (±5%)")
    print(f"   Water balance is acceptable for operational purposes.")
elif abs(balance_error_pct) < 10:
    print(f"⚠️  ACCEPTABLE BALANCE: {balance_error_pct:.2f}% (±10%)")
    print(f"   Water balance shows some discrepancies. Check key measurements.")
else:
    print(f"❌ POOR BALANCE: {balance_error_pct:.2f}% (>10%)")
    print(f"   Water balance has significant errors. Review all measurements and calculations.")

print(f"\n💡 WHAT THIS MEANS:")
print(f"{'─'*100}")
print(f"  • Positive % = More water leaving than entering (possible measurement errors)")
print(f"  • Negative % = More water entering than leaving (storage increase or measurement errors)")
print(f"  • Close to 0% = Good balance (water accounting is accurate)")

print(f"\n📝 NOTES:")
print(f"{'─'*100}")
print(f"  • Total Inflows:       {total_inflows:>15,.0f} m³ from {len(inflow_values)} sources")
print(f"  • Total Outflows:      {total_outflows:>15,.0f} m³ across {len(outflow_values)} flows")
print(f"  • Recirculation:       {total_recirculation:>15,.0f} m³ (internal loops, excluded from balance)")
print(f"  • Difference:          {numerator:>15,.0f} m³ (unaccounted water)")

print(f"\n{'='*100}\n")
