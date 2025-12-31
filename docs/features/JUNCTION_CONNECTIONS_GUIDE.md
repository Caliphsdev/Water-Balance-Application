# 🔗 Line-to-Line Junction Connections

## ✨ New Feature: Connect Flows to Other Flow Lines

You can now create **junction connections** where one flow line connects **directly to another flow line** (not just components). This is perfect for showing:
- Effluent merging into spill lines
- Recirculation joining main supply
- Branch flows merging into trunks
- Any T-junction or Y-junction topology

## 🎯 How It Works

### Visual Appearance
When you create a junction connection, you'll see:
1. **Arrow head** at the junction point (where flows merge)
2. **Small colored circle** marking the exact junction location
3. **Circle color** matches the flow line color (blue/red/orange)

### Example
```
Sewage Treatment → Effluent 46,425 m³ → [●] Spill Line → Outflows
                                         ↑
                                    Junction point
```

## 📋 Step-by-Step Instructions

### Creating a Junction Connection

1. **Start Drawing Mode**
   - Click the "🖊️ Drawing Mode" button
   - Mode activates (button color changes)

2. **Select Source Component**
   - Click on the component you want to flow FROM
   - Example: Click "Sewage Treatment"
   - Component highlights in red

3. **Add Waypoints (Optional)**
   - Click anywhere on canvas to add path points
   - Use waypoints to route around other components
   - Click near (within 8px) of other lines to snap if desired

4. **Finish at Flow Line**
   - Move close to the target flow line (where you want to merge)
   - Click within 15 pixels of the flow line
   - System detects the nearby line and prompts for volume

5. **Enter Flow Details**
   - Dialog appears: "Enter flow volume (m³):"
   - Enter the volume (e.g., 46425)
   - Press Enter or click OK

6. **Junction Created!**
   - Arrow and circle marker appear at junction point
   - Flow line shows with proper color
   - Success message confirms creation

7. **Save Changes**
   - Click "💾 Save Changes" button
   - Junction persists across app restarts

## 🎨 Detection Zones

The system uses two detection thresholds:

| Zone | Distance | Purpose |
|------|----------|---------|
| **Component Anchor** | 30px | Snap to component edge (start/end points) |
| **Line Waypoint** | 8px | Snap waypoint to existing line (visual alignment) |
| **Junction Detection** | 15px | Detect click near line to create junction |

**Tip**: When finishing a draw, move your cursor close to the target line. Within 15px, the system automatically detects it as a junction instead of a component connection.

## ✏️ Editing Junction Connections

### View Junctions
1. Click "Delete Line" button
2. Junction connections show as: `SourceComponent → junction_<id>`
3. Close dialog if you just want to inspect

### Edit Properties
1. Click "Edit Line" button
2. Select junction from listbox
3. Modify:
   - Flow type (clean/wastewater/underground)
   - Color (blue/red/orange/custom)
   - Volume (m³)
   - Bidirectional toggle
4. Changes apply immediately

### Delete Junctions
1. Click "Delete Line" button
2. Select one or more junctions (Ctrl+click for multiple)
3. Click "Delete Selected Lines"
4. Confirm deletion
5. Junctions removed from diagram

## 💾 Data Structure

Junction connections are stored in your diagram JSON with:

```json
{
  "from": "sewage_treatment",
  "to": "junction_1234567890",
  "segments": [
    [100, 200],
    [150, 250],
    [200, 300]
  ],
  "flow_type": "wastewater",
  "volume": 46425,
  "color": "#e74c3c",
  "label": "Effluent 46,425 m³",
  "bidirectional": false,
  "is_junction": true,
  "junction_pos": {
    "x": 200,
    "y": 300
  }
}
```

Key fields:
- `is_junction`: Boolean flag indicating line-to-line connection
- `junction_pos`: Exact {x, y} coordinates where flow merges
- `to`: Virtual junction ID (not a component ID)

## 🎯 Use Cases

### 1. Sewage Effluent Merging
```
Sewage Treatment → Effluent → [●] Spill Line → Losses
```
Shows treated wastewater joining the main spill flow

### 2. Underground Return
```
North Decline → Return Water → [●] Supply Line → Plant
```
Mine dewatering merging back into supply

### 3. Recirculation Loop
```
Dam Storage → Recycle → [●] Main Supply → Distribution
```
Recirculated water joining primary supply

### 4. Branch Consolidation
```
Branch A → Flow 1000 → [●]
Branch B → Flow 2000 → [●] Trunk Line → Main Plant
Branch C → Flow 1500 → [●]
```
Multiple branches merging into main trunk

## ⚙️ Technical Details

### Detection Algorithm
```python
1. User clicks during drawing mode
2. System checks distance to ALL existing flow lines
3. If distance < 15px:
   - Find closest line
   - Calculate exact intersection point
   - Create virtual junction_id
   - Store junction coordinates
4. Else:
   - Check for component anchors (30px)
   - Continue drawing or finish at component
```

### Rendering Pipeline
```python
1. Load edge from JSON
2. Check is_junction flag
3. If junction:
   - Skip to_node validation
   - Use junction_pos for endpoint
   - Draw arrow at junction coordinates
   - Draw colored circle marker (6px diameter)
4. Else:
   - Standard component-to-component rendering
   - Calculate edge intersection for arrow
```

### Color Detection
Junction circles use the same color as the flow line:
- 🔵 **Blue (#3498db)**: Clean water
- 🔴 **Red (#e74c3c)**: Wastewater/effluent
- 🟠 **Orange (#ff9800)**: Underground return

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Junction not detected | Move cursor closer to target line (within 15px) |
| Wrong line targeted | Delete and redraw; try clicking directly on target line |
| Circle not showing | Check saved JSON has `is_junction: true` and `junction_pos` |
| Can't edit junction | Use "Edit Line" dialog; select junction from listbox |
| Junction deleted by accident | No undo yet; redraw from source component |

## 💡 Pro Tips

1. **Plan Your Route**: Add 1-2 waypoints before finishing at junction for cleaner paths
2. **Visual Alignment**: Use the 8px waypoint snap to align with other parallel lines
3. **Color Coordination**: Junction circle color auto-matches flow type for consistency
4. **Descriptive Labels**: Edit volume labels to clarify what's merging (e.g., "Effluent merge")
5. **Test First**: Create junctions in test diagrams before production to verify topology

## 🚀 What's Next?

Future enhancements could include:
- Junction nodes (named merge points)
- Split junctions (one flow splits into multiple)
- Junction flow calculations (sum of inputs = output)
- Junction labels (name the merge point)
- Visual flow direction indicators at junctions

---

**Happy diagramming!** 🌊 Now your flow diagrams can show complex topologies with merging flows!
