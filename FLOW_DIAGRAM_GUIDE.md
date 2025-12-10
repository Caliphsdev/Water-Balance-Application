# 🌊 Interactive Flow Diagram - Complete Guide

## ✨ What's New

### 1. **Auto-Detect Flow Types**
When you create a connection, the system automatically detects what type of water flows through it:

| Flow Type | Color | Detection |
|-----------|-------|-----------|
| **Clean Water** | 🔵 Blue | Default for most connections |
| **Wastewater/Effluent** | 🔴 Red | From Sewage Treatment, to Septic Tank/Losses |
| **Underground Return** | 🟠 Orange | From North Decline/North Shaft |

**Example:** When you connect Sewage Treatment → NDCD, it automatically shows RED (effluent)

### 2. **Control Flow Line Paths (Waypoints)**
Create curved, bendable flow lines! Add waypoints to route connections around obstacles.

## 🎮 How to Use

### Moving Components
```
1. Click on any component
2. Drag it to new position
3. Click "💾 Save Changes"
✓ Component moves, all connected flow lines update automatically!
```

### Creating Connections
```
1. Click "🔗 Connect Components" button
2. Click FIRST component (turns red)
3. Click SECOND component
4. Enter flow value (m³)
5. System auto-selects color based on flow type
6. Click "💾 Save Changes"
✓ Connection created with correct color!
```

### Adding Waypoints to Flow Lines
Flow lines can be straight or curved. Add waypoints to create custom paths:

```
1. Move your mouse cursor over a flow line
2. Press MIDDLE MOUSE BUTTON (scroll wheel click)
3. Click exactly on the line where you want the waypoint
4. System adds waypoint and shows curved line
5. Drag the waypoint circles to reposition
6. Click "💾 Save Changes"
✓ Custom curved flow line saved!
```

### Deleting Waypoints
```
1. Right-click on a waypoint circle
2. Confirm deletion
3. Flow line straightens
```

## 📊 Example Workflow

### Scenario: Rearrange UG2 North Decline Diagram

**Step 1: Move Sewage Treatment to the right**
- Click Sewage Treatment component
- Drag it 200px to the right
- All red flow lines (wastewater) follow it automatically

**Step 2: Create a new connection**
- Click "🔗 Connect"
- Click Offices
- Click NDCD 1-2
- Enter value: 3000
- System shows: RED line (wastewater detected)

**Step 3: Curve the new line**
- Middle-click on the Offices→NDCD line
- Click on the line at a point above/below
- Waypoint added! Blue circle appears
- Drag the blue circle to curve the line
- Release and save

**Step 4: Verify and Save**
- Review all connections with correct colors
- Click "💾 Save Changes"
- Close and reopen app
- Changes persist!

## 🎨 Color Legend

```
🔵 BLUE   = Clean water (supply, distribution)
🔴 RED    = Wastewater/Effluent (sewage, treated waste)
🟠 ORANGE = Underground Return (mine dewatering)
```

## 💡 Pro Tips

1. **Mass Update**: Move a storage tank component → all connected lines follow
2. **Route Around**: Use waypoints to avoid cluttered diagrams
3. **Flow Direction**: Arrows show direction (head of arrow = destination)
4. **Flow Value**: Hover over line label to see actual m³ values
5. **Undo**: Click "↺ Reload" to discard unsaved changes

## 🔧 Technical Details

### Waypoints in JSON
```json
{
  "from": "offices",
  "to": "ndcd",
  "value": 3000,
  "color": "#e74c3c",
  "flow_type": "wastewater",
  "waypoints": [
    {"x": 700, "y": 250},
    {"x": 750, "y": 150}
  ]
}
```

### Flow Type Detection Logic
```python
if from_type == 'sewage' or to_id == 'septic' or to_id == 'losses':
    color = RED (wastewater)
elif from_id contains 'decline' or 'shaft':
    color = ORANGE (dewatering)
else:
    color = BLUE (clean water)
```

## ✅ Checklist

- [ ] **Move a component** → see flow lines follow
- [ ] **Create a connection** → see auto-detected color
- [ ] **Check flow type** → matches component types
- [ ] **Add waypoint** → middle-click on line
- [ ] **Save changes** → click save button
- [ ] **Reload diagram** → verify changes persist

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Flow line color wrong | Delete connection, recreate it |
| Can't add waypoint | Middle-click exactly on the line (not near it) |
| Waypoint won't move | Try middle-clicking the blue circle and dragging |
| Changes didn't save | Did you click "💾 Save Changes"? |

## 🎯 Next Steps

1. **Experiment** with moving components
2. **Create** custom connections between components
3. **Add waypoints** to create curved flows
4. **Save** your layout
5. **Share** the diagram with your team!

---

**Enjoy your interactive water balance diagram!** 💧
