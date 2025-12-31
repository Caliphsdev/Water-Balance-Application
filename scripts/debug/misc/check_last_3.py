import json

with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

print("Last 3 disabled edges:\n")

for edge in diagram["edges"]:
    mapping = edge.get("excel_mapping", {})
    if not mapping.get("enabled"):
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        sheet = mapping.get("sheet", "N/A")
        column = mapping.get("column", "N/A")
        
        print(f"Edge: {from_id} -> {to_id}")
        print(f"  Sheet: {sheet}")
        print(f"  Column: {column}")
        print()
