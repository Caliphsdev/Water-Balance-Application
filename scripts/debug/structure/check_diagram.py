import json

with open("data/diagrams/ug2_north_decline.json") as f:
    diagram = json.load(f)

print("=== FLOW DIAGRAM AREAS ===\n")

# Get unique area codes from edges
areas = set()
for edge in diagram.get("edges", []):
    mapping = edge.get("excel_mapping", {})
    sheet = mapping.get("sheet", "")
    if sheet:
        areas.add(sheet)

print("Sheets referenced by edges:")
for area in sorted(areas):
    print(f"  ✓ {area}")

print(f"\n✓ Total areas: {len(areas)}")

# Count edges by area
area_counts = {}
for edge in diagram.get("edges", []):
    mapping = edge.get("excel_mapping", {})
    sheet = mapping.get("sheet", "")
    if sheet:
        area_counts[sheet] = area_counts.get(sheet, 0) + 1

print("\nEdges per area:")
for sheet in sorted(area_counts):
    print(f"  {sheet}: {area_counts[sheet]} edges")
