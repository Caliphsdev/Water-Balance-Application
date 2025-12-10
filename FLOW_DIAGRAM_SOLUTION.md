# Solution Summary - Flow Diagram Manual Editing

## Problem
- Guest House and Offices consumption components not showing in the diagram
- Need a way to add and edit components without coding
- Main dashboard may have changed

## Solution Provided

### 1. Flow Diagram Editor Tool
**File**: `flow_diagram_editor.py`

A standalone application that lets you manually:
- ✅ Add new components (nodes)
- ✅ Add connections (edges)
- ✅ Edit existing components
- ✅ Delete components
- ✅ View all components in organized table
- ✅ Save changes back to JSON automatically

**Launch with**:
```bash
.\.venv\Scripts\python.exe flow_diagram_editor.py
```

### 2. Complete User Guide
**File**: `FLOW_DIAGRAM_EDITOR_GUIDE.md`

Comprehensive guide covering:
- How to add Guest House consumption
- How to add Offices consumption
- Position and size recommendations
- Color codes for different component types
- How to add connections with flow values
- Troubleshooting tips

### 3. Why Components May Not Be Showing

Possible reasons:
1. **Position outside canvas** - If X or Y is too large, node appears off-screen
2. **Zero width/height** - Node has no visible area
3. **Same color as background** - Makes it invisible
4. **Wrong shape** - Should be 'rect' for most components

### 4. How to Fix Guest House/Offices

Using the editor:
1. Run: `.\.venv\Scripts\python.exe flow_diagram_editor.py`
2. Click "Nodes" tab
3. Look for "guest_house" and "offices" - check their X, Y values
4. If they show Y > 900, they're off-screen
5. Delete them and re-add with correct positions:
   - Guest House: X=750, Y=40
   - Offices: X=920, Y=40
6. Click "Save Diagram"
7. Restart the Water Balance app

### 5. Main Dashboard
The main dashboard (`src/ui/dashboard.py`) appears to be intact. If content changed:
- Check git history with: `git diff src/ui/dashboard.py`
- Or manually compare with backup

### 6. JSON File Location
All changes are saved to:
```
data/diagrams/ug2_north_decline.json
```

You can also edit this file directly in any text editor if needed.

## Next Steps

1. **Test the editor**
   ```bash
   .\.venv\Scripts\python.exe flow_diagram_editor.py
   ```

2. **Verify Guest House and Offices**
   - Open "Nodes" tab
   - Look for both components
   - Check their positions and sizes

3. **If missing, add them**
   - Click "Add Node"
   - Use values from guide
   - Save and restart app

4. **Add connections**
   - Click "Add Edge" tab
   - Add Reservoir → Guest House (16105 m³)
   - Add Reservoir → Offices (14246 m³)
   - Add guest/office to septic connections

5. **Save and verify**
   - Click "Save Diagram"
   - Restart Water Balance app
   - Go to Flow Diagram tab
   - Select UG2N area
   - Verify all components show

## Quick Reference - Component Positions for UG2N

```
Layer 1 - Sources (Y=120-260):
  Borehole: (80, 120)
  Rainfall: (80, 260)

Layer 2 - Storage (Y=200-340):
  Reservoir: (550, 200)
  NDCD: (1120, 270)

Layer 3 - Treatment (Y=140-230):
  Softening: (360, 140)
  Sewage: (860, 230)

Layer 4 - Consumption (Y=40-140):
  Guest House: (750, 40)  ← ADD THIS
  Offices: (920, 40)      ← ADD THIS
  Septic: (1280, 60)
  Losses: (1280, 130)

Layer 5 - Operations (Y=320-400):
  Shaft Area: (760, 320)
  North Decline: (900, 360)
```

## Support
- Use the editor for visual, point-and-click editing
- Refer to `FLOW_DIAGRAM_EDITOR_GUIDE.md` for detailed instructions
- JSON file can be edited directly for advanced changes
