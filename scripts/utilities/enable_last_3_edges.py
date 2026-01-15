"""
Enable the last 3 disabled edges by mapping them to correct Excel columns.
"""

import json

# Load diagram
diagram_path = "data/diagrams/ug2_north_decline.json"
with open(diagram_path, "r", encoding="utf-8") as f:
    diagram = json.load(f)

# Fixes for the 3 disabled edges
FIXES = [
    {
        "from": "oldtsf_new_tsf",
        "to": "oldtsf_nt_rwd",
        "sheet": "Flows_OLDTSF",
        "column": "OLDTSF_NEW_TSF → OLDTSF_NT_RWD"
    },
    {
        "from": "oldtsf_old_tsf",
        "to": "oldtsf_trtd",
        "sheet": "Flows_OLDTSF",
        "column": "OLDTSF_OLD_TSF → OLDTSF_TRTD"
    },
    {
        "from": "stockpile_area",
        "to": "spcd1",
        "sheet": "Flows_Stockpile",
        "column": "STOCKPILE_AREA → SPCD1"
    }
]

enabled_count = 0

for fix in FIXES:
    from_id = fix["from"]
    to_id = fix["to"]
    
    # Find the edge
    for edge in diagram["edges"]:
        if edge.get("from") == from_id and edge.get("to") == to_id:
            mapping = edge.get("excel_mapping", {})
            mapping["enabled"] = True
            mapping["sheet"] = fix["sheet"]
            mapping["column"] = fix["column"]
            enabled_count += 1
            print(f"[OK] {from_id} -> {to_id}")
            print(f"     {fix['sheet']}: {fix['column'].replace(chr(8594), '->')}\n")
            break

# Save updated diagram
with open(diagram_path, "w", encoding="utf-8") as f:
    json.dump(diagram, f, indent=2, ensure_ascii=False)

print("="*80)
print(f"[OK] Enabled {enabled_count} edges")
print(f"[SAVE] Saved to {diagram_path}")
print("="*80)

# Final count
enabled_total = sum(1 for e in diagram["edges"] if e.get("excel_mapping", {}).get("enabled"))
disabled_total = sum(1 for e in diagram["edges"] if not e.get("excel_mapping", {}).get("enabled"))

print(f"\nFINAL STATUS:")
print(f"  [OK] Enabled: {enabled_total}")
print(f"  [X] Disabled: {disabled_total}")
print(f"  [#] Total: {enabled_total + disabled_total}")

if enabled_total == 138:
    print(f"\n[SUCCESS] ALL {enabled_total} FLOW LABELS WILL NOW SHOW DATA!")
