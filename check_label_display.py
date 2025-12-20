import json
import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

# Load the JSON diagram
with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

# Get loader and load volumes
loader = get_flow_volume_loader()
loader.clear_cache()

# Test with UG2N area for December 2025
volumes = loader.get_all_volumes_for_month("UG2N", 2025, 12)

print(f"Loaded {len(volumes)} volumes from Excel for UG2N\n")

# Count edges by mapping status
enabled_edges = []
disabled_edges = []

for edge in diagram.get("edges", []):
    mapping = edge.get("excel_mapping", {})
    if mapping.get("enabled"):
        enabled_edges.append(edge)
    else:
        disabled_edges.append(edge)

print(f"Diagram has {len(enabled_edges)} enabled edges, {len(disabled_edges)} disabled edges\n")

# Check how many enabled edges would get data
matched = 0
unmatched = []

for edge in enabled_edges:
    mapping = edge.get("excel_mapping", {})
    source = edge.get("source", "")
    target = edge.get("target", "")
    flow_key = f"{source} → {target}"
    
    if flow_key in volumes:
        matched += 1
    else:
        unmatched.append(flow_key)

print(f"Of {len(enabled_edges)} enabled edges:")
print(f"  ✅ {matched} would get data from Excel")
print(f"  ❌ {len(unmatched)} would NOT get data\n")

if unmatched:
    print("Unmatched enabled edges:")
    for flow in unmatched[:10]:
        print(f"  {flow}")
    if len(unmatched) > 10:
        print(f"  ... and {len(unmatched) - 10} more")
