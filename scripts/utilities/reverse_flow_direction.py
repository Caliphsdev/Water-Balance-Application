"""
Helper script to safely reverse flow direction in JSON diagram
"""
import json
import sys

def reverse_flow(from_node, to_node):
    """Reverse a flow line direction and update Excel mapping"""
    
    # Load master diagram
    json_file = 'data/diagrams/ug2_north_decline.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    edges = data.get('edges', [])
    
    # Find the flow
    found = False
    for i, edge in enumerate(edges):
        if edge.get('from') == from_node and edge.get('to') == to_node:
            found = True
            print(f"\n✅ Found flow: {from_node} → {to_node}")
            
            # Show current state
            print("\n📋 CURRENT STATE:")
            print(f"   From: {edge['from']}")
            print(f"   To: {edge['to']}")
            
            excel_mapping = edge.get('excel_mapping', {})
            if excel_mapping:
                print(f"   Excel Sheet: {excel_mapping.get('sheet', 'N/A')}")
                print(f"   Excel Column: {excel_mapping.get('column', 'N/A')}")
                print(f"   Enabled: {excel_mapping.get('enabled', False)}")
            
            # Reverse direction
            edge['from'] = to_node
            edge['to'] = from_node
            
            print(f"\n🔄 REVERSED TO:")
            print(f"   From: {edge['from']}")
            print(f"   To: {edge['to']}")
            
            # Update Excel column mapping
            if excel_mapping and excel_mapping.get('column'):
                old_column = excel_mapping['column']
                
                # Try to auto-generate new column name
                if '__TO__' in old_column:
                    # Swap the parts around __TO__
                    parts = old_column.split('__TO__')
                    if len(parts) == 2:
                        new_column = f"{parts[1]}__TO__{parts[0]}"
                        edge['excel_mapping']['column'] = new_column
                        
                        print(f"\n📝 UPDATED EXCEL MAPPING:")
                        print(f"   Old Column: {old_column}")
                        print(f"   New Column: {new_column}")
                        print(f"\n⚠️  WARNING: Check that '{new_column}' exists in Excel!")
                        print(f"   Sheet: {excel_mapping.get('sheet')}")
                        print(f"   If column doesn't exist, you should disable this mapping.")
                else:
                    print(f"\n⚠️  Could not auto-update column name: {old_column}")
                    print(f"   Please update manually in JSON!")
            
            # Save
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Saved changes to {json_file}")
            print(f"\n📌 NEXT STEPS:")
            print(f"   1. Open Excel: test_templates/Water_Balance_TimeSeries_Template.xlsx")
            print(f"   2. Go to sheet: {excel_mapping.get('sheet', 'N/A')}")
            print(f"   3. Verify column '{edge['excel_mapping']['column']}' exists")
            print(f"   4. If not, either:")
            print(f"      - Add the column to Excel, OR")
            print(f"      - Disable mapping: set 'enabled' to false in JSON")
            
            break
    
    if not found:
        print(f"\n❌ Flow not found: {from_node} → {to_node}")
        print(f"\nSearching for similar flows...")
        
        matches = []
        for edge in edges:
            if from_node in edge.get('from', '') or from_node in edge.get('to', ''):
                matches.append(f"  • {edge['from']} → {edge['to']}")
        
        if matches:
            print(f"\nFlows involving '{from_node}':")
            for m in matches[:10]:
                print(m)

def delete_flow(from_node, to_node):
    """Delete a flow line from JSON (Excel data stays intact)"""
    
    json_file = 'data/diagrams/ug2_north_decline.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    edges = data.get('edges', [])
    original_count = len(edges)
    
    # Remove the flow
    new_edges = [e for e in edges if not (e.get('from') == from_node and e.get('to') == to_node)]
    
    if len(new_edges) < original_count:
        data['edges'] = new_edges
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Deleted flow: {from_node} → {to_node}")
        print(f"   Edges: {original_count} → {len(new_edges)}")
        print(f"\n📌 NOTE: Excel data is NOT affected!")
        print(f"   The Excel column still exists and can be remapped later.")
    else:
        print(f"\n❌ Flow not found: {from_node} → {to_node}")

if __name__ == '__main__':
    print("=" * 70)
    print("FLOW DIRECTION TOOL")
    print("=" * 70)
    
    if len(sys.argv) < 4:
        print("\nUsage:")
        print("  Reverse: python reverse_flow_direction.py reverse <from_node> <to_node>")
        print("  Delete:  python reverse_flow_direction.py delete <from_node> <to_node>")
        print("\nExample:")
        print("  python reverse_flow_direction.py reverse oldtsf_offices oldtsf_old_tsf")
        print("  python reverse_flow_direction.py delete oldtsf_offices oldtsf_old_tsf")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    from_node = sys.argv[2]
    to_node = sys.argv[3]
    
    if action == 'reverse':
        reverse_flow(from_node, to_node)
    elif action == 'delete':
        delete_flow(from_node, to_node)
    else:
        print(f"❌ Unknown action: {action}")
        print("   Use 'reverse' or 'delete'")
