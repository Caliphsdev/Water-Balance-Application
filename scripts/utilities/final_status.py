import json

with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

print("="*80)
print("FINAL STATUS - ALL FLOW LABELS")
print("="*80)

enabled = sum(1 for e in diagram["edges"] if e.get("excel_mapping", {}).get("enabled"))
disabled = sum(1 for e in diagram["edges"] if not e.get("excel_mapping", {}).get("enabled"))
total = len(diagram["edges"])

print(f"\n[OK] Enabled edges: {enabled}/{total} ({100*enabled/total:.1f}%)")
print(f"[X] Disabled edges: {disabled}/{total}")

if enabled == total:
    print(f"\n[SUCCESS] ALL {total} FLOW LABELS ARE ENABLED!")
    print(f"[SUCCESS] All flow labels will display data from Excel!")
else:
    print(f"\n[WARNING] {disabled} edges still disabled")

# Count by sheet
sheet_counts = {}
for edge in diagram["edges"]:
    mapping = edge.get("excel_mapping", {})
    if mapping.get("enabled"):
        sheet = mapping.get("sheet", "Unknown")
        sheet_counts[sheet] = sheet_counts.get(sheet, 0) + 1

print(f"\nEnabled edges by sheet:")
for sheet in sorted(sheet_counts.keys()):
    print(f"  {sheet}: {sheet_counts[sheet]} edges")

print("\n" + "="*80)
