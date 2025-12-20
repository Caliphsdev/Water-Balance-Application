"""
Enable the 59 edges that can map to existing Excel columns.
This updates the JSON diagram with correct column mappings.
"""

import json

# Load categorized data
with open("disabled_edges_categorized.json", "r", encoding="utf-8") as f:
    categorized = json.load(f)

# Load diagram
with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

can_map = categorized["can_map"]

print(f"Enabling {len(can_map)} edges with existing Excel columns...\n")

enabled_count = 0

# Build a lookup for faster matching
edge_lookup = {}
for i, edge in enumerate(diagram["edges"]):
    from_id = edge.get("from", "")
    to_id = edge.get("to", "")
    key = f"{from_id}→{to_id}"
    edge_lookup[key] = i

# Enable edges
for item in can_map:
    from_id = item["from"]
    to_id = item["to"]
    expected_column = item["expected_column"]
    sheet = item["sheet"]
    
    key = f"{from_id}→{to_id}"
    
    if key in edge_lookup:
        edge_idx = edge_lookup[key]
        edge = diagram["edges"][edge_idx]
        mapping = edge.get("excel_mapping", {})
        
        # Update mapping
        mapping["enabled"] = True
        mapping["sheet"] = sheet
        mapping["column"] = expected_column
        
        enabled_count += 1
        # Replace arrow for console output
        display_column = expected_column.replace("→", "->")
        print(f"[OK] {sheet}")
        print(f"   {from_id} -> {to_id}")
        print(f"   Column: {display_column}\n")

# Save updated diagram
with open("data/diagrams/ug2_north_decline.json", "w", encoding="utf-8") as f:
    json.dump(diagram, f, indent=2, ensure_ascii=False)

print("="*80)
print(f"[OK] Enabled {enabled_count} edges")
print(f"[SAVE] Saved to data/diagrams/ug2_north_decline.json")
print("="*80)

# Count current status
enabled_total = sum(1 for e in diagram["edges"] if e.get("excel_mapping", {}).get("enabled"))
disabled_total = sum(1 for e in diagram["edges"] if not e.get("excel_mapping", {}).get("enabled"))

print(f"\nNew status:")
print(f"  [OK] Enabled: {enabled_total}")
print(f"  [X] Disabled: {disabled_total}")
print(f"  [#] Total: {enabled_total + disabled_total}")
