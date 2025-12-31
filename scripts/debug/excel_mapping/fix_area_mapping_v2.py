import json

print("Fixing area mappings with better logic...")

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Better area matching - be more specific
def get_area_sheet(from_node, to_node):
    """Determine the correct Excel sheet based on node names"""
    from_lower = from_node.lower()
    to_lower = to_node.lower()
    combined = from_lower + ' ' + to_lower
    
    # Most specific matches first
    if 'stockpile' in from_lower or 'stockpile' in to_lower or 'spcd' in from_lower or 'spcd' in to_lower:
        if 'ug2s' not in combined and 'mers' not in combined:
            return 'Flows_STOCKPILE'
    
    if 'oldtsf' in from_lower or 'oldtsf' in to_lower:
        if 'mers' not in combined and 'ug2s' not in combined:
            return 'Flows_OLDTSF'
    
    if 'ug2plant' in from_lower or 'ug2plant' in to_lower or 'cprwsd1' in from_lower or 'cprwsd1' in to_lower:
        return 'Flows_UG2PLANT'
    
    if 'merplant' in from_lower or 'merplant' in to_lower or 'mpswd' in from_lower or 'mpswd' in to_lower or 'mprwsd' in from_lower or 'mprwsd' in to_lower:
        return 'Flows_MERPLANT'
    
    if 'ug2s' in from_lower or 'ug2s' in to_lower:
        return 'Flows_UG2S'
    
    if 'mers' in from_lower or 'mers' in to_lower or 'mdcd' in from_lower or 'mdcd' in to_lower:
        return 'Flows_MERS'
    
    if 'mern' in from_lower or 'mern' in to_lower or 'merensky_north' in from_lower or 'merensky_north' in to_lower:
        return 'Flows_MERN'
    
    # Default to UG2N for shared/junction nodes
    return 'Flows_UG2N'

fixed_count = 0
for i, edge in enumerate(edges):
    from_node = edge.get('from', '')
    to_node = edge.get('to', '')
    
    correct_sheet = get_area_sheet(from_node, to_node)
    
    # Update mapping
    edge['excel_mapping'] = {
        'enabled': True,
        'sheet': correct_sheet,
        'column': edge.get('excel_mapping', {}).get('column', '')
    }
    fixed_count += 1

# Save
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"✅ Fixed {fixed_count} edges")
print("✅ Remapping complete")
