# Flow Diagram Editor - User Guide

## Overview
The Flow Diagram Editor allows you to manually add and edit flow diagram components without writing code. This is perfect for customizing your UG2 North Decline Area diagram.

## How to Use

### 1. Start the Editor
```bash
cd C:\PROJECTS\Water-Balance-Application
.\.venv\Scripts\python.exe flow_diagram_editor.py
```

### 2. The Editor Window
The editor has two main tabs:

#### Tab 1: "Nodes (Components)" 
This shows all components in your diagram:
- **Component ID**: Unique identifier (e.g., "guest_house", "offices")
- **Label**: What appears in the diagram box
- **X, Y**: Position on the canvas
- **Width, Height**: Size of the box
- **Type**: The category (source, storage, treatment, consumption, process, loss)

#### Tab 2: "Edges (Connections)"
This shows all flow connections:
- **From**: Starting component ID
- **To**: Ending component ID  
- **Value**: Flow amount in m³
- **Label**: Text shown on the connection line
- **Color**: Hex color code (e.g., #4b78a8 for blue, #e74c3c for red)

### 3. Common Tasks

#### Adding a New Component (Guest House Example)
1. Click "Add Node" button
2. Fill in these fields:
   - **ID**: `guest_house`
   - **Label**: `GUEST HOUSE\n(Consumption)` (use \n for line breaks)
   - **Type**: `consumption`
   - **X**: `750` (position from left)
   - **Y**: `40` (position from top)
   - **Width**: `130`
   - **Height**: `50`
   - **Fill**: `#5d88b6` (light blue)
   - **Outline**: `#2c5d8a` (dark blue)
3. Click "Save Node"

#### Adding a Connection (Reservoir to Guest House)
1. Click "Add Edge" button
2. Fill in:
   - **From**: `reservoir`
   - **To**: `guest_house`
   - **Value**: `16105`
   - **Label**: `16 105`
   - **Color**: `#4b78a8`
3. Click "Save Connection"

#### Editing Components
1. Find the component in the Nodes tab
2. Right-click and select it
3. Delete it with "Delete Selected"
4. Add it again with corrected values

#### Deleting Components
1. Click on the row in Nodes or Edges tab
2. Click "Delete Selected"

### 4. Color Codes (Hex Colors)

**Sources**:
- Boreholes: `#8ab7e6` (light blue)
- Rivers: `#b7d4f3` (very light blue)

**Treatment/Process**:
- Softening/Treatment: `#e89c3d` (orange)

**Storage**:
- Reservoir: `#4b78a8` (dark blue)
- Storage groups: `#3f6ea3` (darker blue)

**Operations**:
- Decline: `#a34136` (red)
- Shaft: `#b04c40` (lighter red)

**Consumption**:
- Guest House/Offices: `#5d88b6` (light blue)
- Septic: `#ffffff` (white with red outline `#c40000`)

**Losses**:
- `#ffffff` (white with black outline `#000000`)

**Flow Line Colors**:
- Clean water: `#4b78a8` (blue)
- Dirty/Effluent: `#e74c3c` (red)
- Losses: `#000000` (black)

### 5. Position Tips
- **X values**: Space components 150-200 pixels apart horizontally
- **Y values**: Space components 60-80 pixels apart vertically
- **Canvas size**: Default is 1800 x 900
- **Standard width**: 130-150 pixels for normal components
- **Standard height**: 40-50 pixels

### 6. Saving Your Work
1. Make all your changes
2. Click "Save Diagram" button
3. The diagram JSON is saved automatically
4. Restart the Water Balance app to see changes

### 7. Example UG2 North Decline Components

**Current Structure Should Have:**

Sources Layer (Y=120-260):
- Borehole Abstraction (80, 120)
- Direct Rainfall (80, 260)

Storage Layer (Y=200-340):
- Reservoir (550, 200) - OVAL shape
- NDCD 1-2/NDSWD1 (1120, 270) - OVAL shape

Treatment Layer (Y=140-230):
- Softening Plant (360, 140)
- Sewage Treatment (860, 230)

Consumption Layer (Y=40-140):
- Guest House (750, 40) ← Should be visible
- Offices (920, 40) ← Should be visible
- Septic Tank (1280, 60)
- Losses (1280, 130)

Operations Layer (Y=320-400):
- North Decline Shaft Area (760, 320)
- North Decline (900, 360)

### 8. Troubleshooting

**Components not visible?**
- Check X, Y positions - make sure they're within canvas (0-1800, 0-900)
- Check Width, Height - shouldn't be 0
- Check Fill color isn't same as canvas background

**Connections crossing?**
- The routing algorithm automatically prevents crossings
- If still crossing, adjust component positions slightly

**Changes not appearing in app?**
- Save the diagram first (click "Save Diagram")
- Close and restart the Water Balance app
- Navigate to Flow Diagram tab

### 9. JSON File Location
The diagram file is stored at:
```
C:\PROJECTS\Water-Balance-Application\data\diagrams\ug2_north_decline.json
```

You can also edit this file directly in a text editor if needed.

### 10. Getting Help
If something doesn't work:
1. Check the console for error messages
2. Verify all numeric values (X, Y, Width, Height, Value)
3. Verify component IDs have no spaces or special characters
4. Make sure "From" and "To" IDs match existing component IDs
