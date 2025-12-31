import json

with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

enabled = sum(1 for e in diagram["edges"] if e.get("excel_mapping", {}).get("enabled"))
disabled = sum(1 for e in diagram["edges"] if not e.get("excel_mapping", {}).get("enabled"))

print(f"Edge Status Summary:")
print(f"  ✅ Enabled (will show data): {enabled}")
print(f"  ❌ Disabled (no data): {disabled}")
print(f"  📊 Total edges: {enabled + disabled}")
