"""
Restructure Flow Diagram:
1. Remove Merensky North Area completely
2. Split Old TSF Area into Old TSF and New TSF separate areas
"""
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def restructure_diagram():
    """Restructure the flow diagram JSON"""
    
    diagram_path = Path(__file__).parent.parent / "data" / "diagrams" / "ug2_north_decline.json"
    backup_path = diagram_path.with_suffix('.json.backup')
    
    print(f"📂 Loading diagram from: {diagram_path}")
    
    # Backup original
    with open(diagram_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Backup saved to: {backup_path}")
    
    # 1. Remove Merensky North title
    if 'merensky_title' in data:
        del data['merensky_title']
        print("🗑️  Removed Merensky North title")
    
    # 2. Remove Merensky North zone background
    data['zone_bg'] = [z for z in data['zone_bg'] if 'Merensky North' not in z.get('name', '')]
    print("🗑️  Removed Merensky North zone background")
    
    # 3. Remove all Merensky North nodes
    merensky_north_nodes = [
        'bh_mcgwa', 'rainfall_merensky', 'softening_merensky', 
        'offices_merensky', 'merensky_north_decline', 'merensky_north_shaft',
        'ndcd_merensky', 'losses_merensky', 'consumption_merensky',
        'spill_merensky', 'evaporation_merensky', 'dust_suppression_merensky'
    ]
    
    original_node_count = len(data['nodes'])
    data['nodes'] = [n for n in data['nodes'] if n['id'] not in merensky_north_nodes]
    removed_nodes = original_node_count - len(data['nodes'])
    print(f"🗑️  Removed {removed_nodes} Merensky North nodes")
    
    # 4. Remove all edges connected to Merensky North nodes
    original_edge_count = len(data['edges'])
    data['edges'] = [
        e for e in data['edges'] 
        if e['from'] not in merensky_north_nodes and e['to'] not in merensky_north_nodes
    ]
    removed_edges = original_edge_count - len(data['edges'])
    print(f"🗑️  Removed {removed_edges} edges connected to Merensky North")
    
    # 5. Split Old TSF Area into Old TSF and New TSF
    # Find Old TSF zone
    old_tsf_zone = None
    for zone in data['zone_bg']:
        if 'Old TSF Area' in zone.get('name', ''):
            old_tsf_zone = zone
            break
    
    if old_tsf_zone:
        # Calculate split point (roughly in middle)
        zone_height = old_tsf_zone['height']
        split_height = zone_height // 2
        
        # Create Old TSF zone (top half)
        old_tsf_new_zone = {
            "name": "Old TSF",
            "x": old_tsf_zone['x'],
            "y": old_tsf_zone['y'],
            "width": old_tsf_zone['width'],
            "height": split_height,
            "color": "#e8f5e9"  # Light green
        }
        
        # Create New TSF zone (bottom half)
        new_tsf_zone = {
            "name": "New TSF",
            "x": old_tsf_zone['x'],
            "y": old_tsf_zone['y'] + split_height,
            "width": old_tsf_zone['width'],
            "height": zone_height - split_height,
            "color": "#fff9c4"  # Light yellow
        }
        
        # Remove old zone and add two new ones
        data['zone_bg'] = [z for z in data['zone_bg'] if 'Old TSF Area' not in z.get('name', '')]
        data['zone_bg'].append(old_tsf_new_zone)
        data['zone_bg'].append(new_tsf_zone)
        
        print(f"✂️  Split Old TSF Area into:")
        print(f"   - Old TSF (y: {old_tsf_new_zone['y']}, height: {old_tsf_new_zone['height']})")
        print(f"   - New TSF (y: {new_tsf_zone['y']}, height: {new_tsf_zone['height']})")
        
        # Update title
        data['oldtsf_title'] = "Old TSF"
        data['newtsf_title'] = "New TSF"
        
        print("📝 Updated titles: Old TSF and New TSF")
    
    # 6. Adjust zones after Merensky North removal
    # Move all zones after Merensky North up by the removed zone height (420px)
    merensky_north_height = 420
    
    # Find zones that need to be moved up
    zones_to_adjust = []
    for zone in data['zone_bg']:
        # If zone starts after where Merensky North was (y >= 470), move it up
        if zone['y'] >= 470:
            zone['y'] -= merensky_north_height
            zones_to_adjust.append(zone['name'])
    
    if zones_to_adjust:
        print(f"⬆️  Moved zones up by {merensky_north_height}px: {', '.join(zones_to_adjust)}")
    
    # 7. Adjust node positions after Merensky North removal
    nodes_adjusted = 0
    for node in data['nodes']:
        # If node is after Merensky North area, move it up
        if node['y'] >= 470:
            node['y'] -= merensky_north_height
            nodes_adjusted += 1
    
    if nodes_adjusted:
        print(f"⬆️  Moved {nodes_adjusted} nodes up by {merensky_north_height}px")
    
    # 8. Adjust edge segments after position changes
    edges_adjusted = 0
    for edge in data['edges']:
        adjusted = False
        for segment in edge.get('segments', []):
            # If segment point is after Merensky North, move it up
            if segment[1] >= 470:
                segment[1] -= merensky_north_height
                adjusted = True
        
        # Adjust label positions if they exist
        if 'label_pos' in edge and isinstance(edge['label_pos'], dict):
            if edge['label_pos'].get('y', 0) >= 470:
                edge['label_pos']['y'] -= merensky_north_height
                adjusted = True
        
        # Adjust recirculation positions
        if 'recirculation_pos' in edge and isinstance(edge['recirculation_pos'], dict):
            if edge['recirculation_pos'].get('y', 0) >= 470:
                edge['recirculation_pos']['y'] -= merensky_north_height
                adjusted = True
        
        # Adjust junction positions
        if 'junction_pos' in edge and isinstance(edge['junction_pos'], dict):
            if edge['junction_pos'].get('y', 0) >= 470:
                edge['junction_pos']['y'] -= merensky_north_height
                adjusted = True
        
        if 'junction_start_pos' in edge and isinstance(edge['junction_start_pos'], dict):
            if edge['junction_start_pos'].get('y', 0) >= 470:
                edge['junction_start_pos']['y'] -= merensky_north_height
                adjusted = True
        
        if adjusted:
            edges_adjusted += 1
    
    if edges_adjusted:
        print(f"⬆️  Adjusted {edges_adjusted} edge segments/positions")
    
    # 9. Update overall diagram height
    data['height'] = data['height'] - merensky_north_height
    print(f"📏 Updated diagram height to: {data['height']}")
    
    # 10. Save restructured diagram
    with open(diagram_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Restructuring complete!")
    print(f"📊 Final statistics:")
    print(f"   - Zones: {len(data['zone_bg'])}")
    print(f"   - Nodes: {len(data['nodes'])}")
    print(f"   - Edges: {len(data['edges'])}")
    print(f"\n⚠️  Important: Excel mappings for Merensky North flows have been removed.")
    print(f"   All other Excel mappings are preserved intact.")
    print(f"\n💡 Backup saved to: {backup_path}")
    print(f"   If you need to restore, copy the backup back to the original location.")

if __name__ == '__main__':
    try:
        restructure_diagram()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
