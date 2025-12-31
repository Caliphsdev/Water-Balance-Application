# UI Feature: Add Components (Nodes) Through the Diagram Editor

## Overview
You can now **add new components directly through the UI** without manually editing JSON files. This feature integrates seamlessly with the existing diagram editor.

## How to Use

### Step 1: Open the Flow Diagram
1. Run the app: `python src/main.py`
2. Navigate to **Flow Diagram** tab
3. Select your area (Old TSF, New TSF, UG2 Plant, etc.)

### Step 2: Add a New Component
Click the **➕ Add Component** button in the Components section of the toolbar.

![Button Location]
```
🔧 COMPONENTS: [➕ Add Component] [✏️ Edit Node] [🗑️ Delete Node] [🔒 Lock/Unlock]
```

### Step 3: Fill in Component Details

A dialog will appear with the following fields:

| Field | Description | Example |
|-------|-------------|---------|
| **Component ID** | Unique identifier (no spaces) | `oldtsf_treatment_tank` |
| **Label** | Display name in diagram | `TREATMENT TANK` |
| **Position X** | Horizontal position (pixels) | `500` |
| **Position Y** | Vertical position (pixels) | `1800` |
| **Width** | Component width | `150` |
| **Height** | Component height | `50` |
| **Type** | Category of component | `process`, `storage`, `source`, etc. |
| **Shape** | Visual shape | `rect`, `oval`, `diamond` |
| **Fill Color** | Background color (hex) | `#f39c12` |
| **Outline Color** | Border color (hex) | `#c46f00` |

### Step 4: Click "✅ Create"
The component will be added to the diagram immediately.

### Step 5: Save Your Changes
Click **💾 Save** to persist changes to the JSON file.

---

## Component Types Reference

```
source           → Blue boxes (boreholes, water intake)
process          → Brown boxes (processing units)
storage          → Oval shapes (tanks, reservoirs)
consumption      → Blue boxes (offices, end users)
building         → Building-like boxes
treatment        → Orange boxes (sewage treatment)
plant            → Gray boxes (concentrator plant)
tsf              → Orange boxes (tailings storage facility)
reservoir        → Oval shapes (water storage)
loss             → White boxes (losses, discharge)
discharge        → White boxes (environmental discharge)
```

---

## Component Shape Options

| Shape | Best For |
|-------|----------|
| **rect** | Most components (default) |
| **oval** | Storage tanks, reservoirs |
| **diamond** | Decision points, distribution nodes |

---

## Color Codes (Hex)

Common colors by flow type:

```
Clean water:        #4b78a8 (blue)
Process/Orange:     #f39c12 (orange)
Losses:             #ffffff (white)
Underground:        #148f77 (teal)
Buildings:          #5dade2 (light blue)
Plants/Systems:     #95a5a6 (gray)
TSF/Storage:        #f9a825 (gold)
```

---

## Example: Adding a Treatment Tank

**Scenario:** Add a treatment tank to the Old TSF area that processes water before discharge.

### Input:
```
Component ID:    oldtsf_treatment_tank
Label:          TREATMENT TANK
Position X:     700
Position Y:     1900
Width:          180
Height:         60
Type:           treatment
Shape:          rect
Fill Color:     #f39c12
Outline Color:  #c46f00
```

### Result:
- ✅ Component appears in diagram at (700, 1900)
- ✅ Orange colored box with black outline
- ✅ Labeled "TREATMENT TANK"
- ✅ Ready to connect to flowlines

---

## Next Steps After Adding a Component

### 1. Connect with Flowlines
Use the **✏️ Draw** button in the Flowlines section to:
- Draw lines from/to your new component
- Set flow types (clean, waste, etc.)
- Configure Excel mappings

### 2. Add Excel Mapping
After creating connecting flowlines, add corresponding Excel columns to:
- Sheet: `Flows_OLDTSF`, `Flows_UG2P`, etc.
- Column header: `COMPONENT_FROM → COMPONENT_TO`
- Add volume data in rows 4+

### 3. Edit Properties
Select the component and click **✏️ Edit Node** to modify:
- Label text
- Size and colors
- Position and shape
- Lock state

### 4. Delete if Needed
Select the component and click **🗑️ Delete Node** to:
- Remove the component
- Automatically remove all connected flowlines
- Clean up all references

---

## Tips & Best Practices

✓ **Use consistent naming:** `area_component_type` (e.g., `ug2plant_softening_plant`)

✓ **Position matters:** Place components logically within their zone for clarity

✓ **Lock after placement:** Use **🔒 Lock/Unlock** to prevent accidental moves

✓ **Save frequently:** Click **💾 Save** after each major change

✓ **Check for duplicates:** Component IDs must be unique across the entire diagram

✓ **Add flowlines immediately:** Connect your new component with flowlines right away

✓ **Update Excel mappings:** Without Excel columns, the component won't have data

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Component doesn't appear | Check position X/Y (must be within canvas bounds) |
| Can't connect flowlines | Component ID must exist and be spelled correctly |
| Changes lost after closing | Click **💾 Save** before closing the app |
| Duplicate ID error | Choose a unique component ID not already in diagram |
| Component off-screen | Adjust X/Y position and use zoom buttons to verify |

---

## Integration with Existing Features

This new feature works seamlessly with:

- ✅ **Component Rename System** - Rename components after creation
- ✅ **Flowline Drawing** - Connect to new components immediately
- ✅ **Excel Mapping** - Add data columns for new components
- ✅ **Component Properties** - Edit size, color, shape anytime
- ✅ **Save/Load** - All changes persisted to JSON

---

## File Locations

- **JSON Diagram:** `data/diagrams/ug2_north_decline.json`
- **Excel Template:** `test_templates/Water_Balance_TimeSeries_Template.xlsx`
- **Dashboard Code:** `src/ui/flow_diagram_dashboard.py`

---

**Now you can build your diagram entirely through the UI! No more manual JSON editing needed.**
