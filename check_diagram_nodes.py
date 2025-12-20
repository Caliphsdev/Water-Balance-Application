import json

# Get actual nodes used in diagram
with open("data/diagrams/ug2_north_decline.json") as f:
    diagram = json.load(f)

# Get all node IDs from the diagram
nodes_in_diagram = set()
for node in diagram.get("nodes", []):
    nodes_in_diagram.add(node.get("id", ""))

print("=== DIAGRAM NODE IDS ===\n")
print(f"Total nodes in diagram: {len(nodes_in_diagram)}\n")

# Sample
print("Sample of nodes in diagram:")
for i, node in enumerate(sorted(nodes_in_diagram)[:20]):
    print(f"  {i+1}. {node}")

# Check for old patterns
old_patterns = ["MERENSKY", "MERSN", "MERSO", "_OLD"]
print(f"\n\nSearching for OLD PATTERNS in diagram nodes: {old_patterns}")

found_old = {}
for node in nodes_in_diagram:
    for pattern in old_patterns:
        if pattern.lower() in node.lower():
            if pattern not in found_old:
                found_old[pattern] = []
            found_old[pattern].append(node)

if found_old:
    print("\n❌ OLD PATTERNS FOUND IN DIAGRAM:")
    for pattern, nodes in found_old.items():
        print(f"  {pattern}: {len(nodes)} nodes")
        for node in nodes[:3]:
            print(f"    - {node}")
else:
    print("\n✓ No old patterns in diagram nodes")

# Check for unused Flows_MERN
print("\n\n=== UNUSED AREAS CHECK ===")
areas_in_template = ["Flows_OLDTSF", "Flows_UG2P", "Flows_UG2S", "Flows_UG2N", 
                     "Flows_MERN", "Flows_MERP", "Flows_MERS", "Flows_STOCKPILE"]
areas_in_diagram = set()
for edge in diagram.get("edges", []):
    sheet = edge.get("excel_mapping", {}).get("sheet", "")
    if sheet:
        areas_in_diagram.add(sheet)

print("\nTemplate areas not used by diagram:")
for area in sorted(areas_in_template):
    if area not in areas_in_diagram:
        print(f"  ⚠️  {area} (has data but no edges map to it)")
    else:
        print(f"  ✓ {area}")
