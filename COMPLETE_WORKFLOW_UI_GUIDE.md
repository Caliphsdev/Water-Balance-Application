# Complete Workflow: Build Your Diagram in the UI

## New Capabilities (v2.0)

You can now **build and manage your entire flow diagram through the UI** without touching JSON files!

### What's Possible Now

```
✅ Add components (nodes)
✅ Edit component properties
✅ Delete components
✅ Lock/unlock components
✅ Draw flowlines
✅ Edit flowline properties
✅ Add recirculation loops
✅ Map to Excel columns
✅ Validate mappings
✅ All through the UI!
```

---

## Complete Workflow Example

### Scenario: Build Mini Water System from Scratch

#### Step 1: Add Source Component

1. **Open app** → Go to Flow Diagram tab
2. **Select area** (e.g., "Old TSF")
3. **Click ➕ Add Component**
4. **Fill form:**
   ```
   Component ID:    source_borehole
   Label:          BOREHOLE
   Position X:     100
   Position Y:     200
   Width:          150
   Height:         40
   Type:           source
   Shape:          rect
   Fill Color:     #8ab7e6
   Outline Color:  #2c5d8a
   ```
5. **Click ✅ Create**

**Result:** Blue borehole component appears at (100, 200)

---

#### Step 2: Add Processing Component

1. **Click ➕ Add Component**
2. **Fill form:**
   ```
   Component ID:    process_tank
   Label:          PROCESSING TANK
   Position X:     400
   Position Y:     200
   Width:          150
   Height:         60
   Type:           process
   Shape:          rect
   Fill Color:     #f39c12
   Outline Color:  #c46f00
   ```
3. **Click ✅ Create**

**Result:** Orange processing tank at (400, 200)

---

#### Step 3: Add Storage Component

1. **Click ➕ Add Component**
2. **Fill form:**
   ```
   Component ID:    storage_tank
   Label:          STORAGE
   Position X:     700
   Position Y:     200
   Width:          120
   Height:         80
   Type:           storage
   Shape:          oval
   Fill Color:     #4b78a8
   Outline Color:  #1f4d7a
   ```
3. **Click ✅ Create**

**Result:** Blue storage tank (oval) at (700, 200)

---

#### Step 4: Add Loss Component

1. **Click ➕ Add Component**
2. **Fill form:**
   ```
   Component ID:    losses
   Label:          EVAPORATION
   Position X:     1000
   Position Y:     200
   Width:          150
   Height:         40
   Type:           loss
   Shape:          rect
   Fill Color:     #ffffff
   Outline Color:  #000000
   ```
3. **Click ✅ Create**

**Result:** White loss box at (1000, 200)

---

#### Step 5: Connect Components with Flowlines

**Draw: Source → Processing**

1. **Click ✏️ Draw button** (in Flowlines section)
2. **Click on source_borehole** (starting point)
3. **Click on process_tank** (ending point)
4. **Click on canvas to place segments:**
   - (200, 200) → down to (200, 250)
   - (200, 250) → right to (400, 250)
   - (400, 250) → up to (400, 230)

5. **Click ✏️ Edit** button to configure:
   - **Flow Type:** clean
   - **Label:** "Source Flow"
   - **Excel Mapping:**
     - Sheet: Flows_OLDTSF
     - Column: SOURCE_BOREHOLE → PROCESS_TANK

**Draw: Processing → Storage**

1. **Click ✏️ Draw**
2. **Click on process_tank**
3. **Click on storage_tank**
4. **Place segments connecting them**
5. **Configure as:**
   - Flow Type: clean
   - Excel Mapping: PROCESS_TANK → STORAGE_TANK

**Draw: Storage → Loss**

1. **Click ✏️ Draw**
2. **Click on storage_tank**
3. **Click on losses**
4. **Place segments**
5. **Configure as:**
   - Flow Type: evaporation
   - Color: #000000 (black)
   - Excel Mapping: STORAGE_TANK → EVAPORATION

---

#### Step 6: Add Excel Data Columns

Open `test_templates/Water_Balance_TimeSeries_Template.xlsx`

Go to **Flows_OLDTSF** sheet:

Add three columns (in Row 3, starting after existing data):

```
Column N (Row 3):  SOURCE_BOREHOLE → PROCESS_TANK
Column N (Row 4):  1000  (volume in m³)
Column N (Row 5):  1100
Column N (Row 6):  950

Column O (Row 3):  PROCESS_TANK → STORAGE_TANK
Column O (Row 4):  950
Column O (Row 5):  1050
Column O (Row 6):  900

Column P (Row 3):  STORAGE_TANK → EVAPORATION
Column P (Row 4):  50
Column P (Row 5):  50
Column P (Row 6):  50
```

---

#### Step 7: Validate Mappings

1. **In Flow Diagram, click 🔍 Validate**
2. **Check for green checkmarks:**
   ```
   ✓ SOURCE_BOREHOLE → PROCESS_TANK: Column found
   ✓ PROCESS_TANK → STORAGE_TANK: Column found
   ✓ STORAGE_TANK → EVAPORATION: Column found
   ```

---

#### Step 8: Load Volume Data

1. **Set Year/Month in toolbar**
2. **Click 🔄 Load Excel**
3. **Volumes should appear on flowlines:**
   ```
   Source → Processing:  1000 m³
   Processing → Storage: 950 m³
   Storage → Loss:       50 m³
   ```

---

#### Step 9: Save Everything

1. **Click 💾 Save**
2. **Confirmation shows:**
   ```
   JSON file updated with:
   • 4 nodes (components)
   • 3 edges (flowlines)
   • Excel mappings
   ```

---

#### Step 10: Run Calculations

1. **Go to Calculations tab**
2. **Click ✓ Calculate**
3. **Results show:**
   - Inflow: 1000 m³
   - Processing: 950 m³
   - Storage: 0 m³ (balanced)
   - Losses: 50 m³

---

## UI Components Reference

### Add Component Dialog

```
Click: ➕ Add Component

Form opens with fields:
├─ Component ID (required, unique)
├─ Label (display name)
├─ Position X (0-2000)
├─ Position Y (0-3500)
├─ Width (40-400)
├─ Height (20-200)
├─ Type (dropdown: 10 options)
├─ Shape (dropdown: rect, oval, diamond)
├─ Fill Color (hex code)
└─ Outline Color (hex code)

Actions:
├─ ✅ Create (adds to diagram)
└─ ✖ Cancel (discards)

Result:
└─ Component appears instantly
   + Success message
   + Ready to connect
```

### Edit Node Dialog

```
Click: ✏️ Edit Node (after selecting component)

Form opens with:
├─ Current label
├─ Width/Height controls
├─ Fill/Outline colors
├─ Shape selector
├─ Type selector

Actions:
├─ 💾 Save Changes
└─ ✖ Cancel

Result:
└─ Component updated in diagram
```

### Draw Flowline Interface

```
Click: ✏️ Draw (in Flowlines section)

Steps:
1. Click source component
2. Click on canvas to add path segments
3. Click target component
4. Right-click to finish

Dialog opens to configure:
├─ Flow type (clean, waste, etc.)
├─ Label
├─ Excel mapping
└─ Bidirectional option

Actions:
├─ ✅ Save
└─ ✖ Cancel
```

---

## Tips & Best Practices

### Organization Tips

```
✓ Group by area (all OldTSF on left, etc.)
✓ Use consistent spacing
✓ Place sources on left, losses on right
✓ Group related components
✓ Keep components unlocked while designing
✓ Lock components after positioning
```

### Naming Tips

```
✓ Use descriptive IDs: oldtsf_treatment_tank
✓ Use UPPERCASE labels: TREATMENT TANK
✓ Follow area naming: [area]_[component]
✓ Keep IDs unique across entire diagram
✓ Use underscores, not spaces or dashes
```

### Color Tips

```
✓ Use consistent colors by type
✓ Blue for storage/reservoirs
✓ Orange for processing/treatment
✓ Red/pink for waste
✓ White for losses
✓ Green for sustainable/treatment
✓ Gray for major plants
```

### Excel Column Tips

```
✓ Column header format: [FROM] → [TO]
✓ Header in Row 3 only
✓ Data starts in Row 4
✓ Use numbers, not text
✓ Keep headers consistent with JSON
✓ Add data in chronological order
```

---

## Complete Checklist for New Area

Building a complete new area from scratch:

```
PLANNING:
☐ Define all components needed
☐ Sketch layout on paper
☐ List all connections (flowlines)
☐ Determine data sources
☐ Plan Excel columns

IMPLEMENTATION:
☐ Add all components with Add Component
☐ Position each one
☐ Lock components after placing
☐ Draw all flowlines
☐ Configure flowline properties
☐ Set up Excel mappings

VALIDATION:
☐ Run Validate to check mappings
☐ Check that all flows have data
☐ Verify flow directions
☐ Test with sample data
☐ Run calculations

FINALIZATION:
☐ Save JSON changes
☐ Add all Excel data
☐ Document component purposes
☐ Test calculations
☐ Archive version
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Component doesn't appear | Check Position X/Y within bounds |
| Flowline won't connect | Ensure both components exist |
| Excel column not found | Check header exactly matches JSON |
| Calculations show 0 | Verify Excel has data in rows 4+ |
| Changes disappeared | Must click 💾 Save to persist |
| Can't move component | Component might be locked - use 🔒 Lock/Unlock |
| Too many components | Use zoom buttons to see full diagram |

---

## Performance Tips

✓ **Create components in groups** (finish all adds, then all draws)  
✓ **Minimize window resizing** during editing  
✓ **Lock components** to prevent accidental moves  
✓ **Save frequently** (every 10 changes)  
✓ **Use zoom strategically** for precision positioning  

---

## Advanced Features Available

### Component Rename System

```
When you need to rename a component across:
✓ JSON diagram
✓ All connected flowlines  
✓ Excel columns
✓ All 8 flow sheets

Use: python component_rename_manager.py --dry-run
Then: python component_rename_manager.py
```

### Excel Mapping Validation

```
Click: 🔍 Validate

Shows:
✓ All columns found
✗ Missing columns
⚠️ Encoding issues
✓ Data present

Helps debug connectivity issues
```

### Recirculation Loops

```
Click: ♻️ Recirculation (in Flowlines)

Allows:
✓ Feedback loops
✓ Recycled flows
✓ Return to processing
✓ Custom path drawing
```

---

## File Organization

After building your diagram:

```
data/diagrams/
  └─ ug2_north_decline.json       (Updated with your components)

test_templates/
  └─ Water_Balance_TimeSeries_Template.xlsx
      ├─ Flows_OLDTSF
      ├─ Flows_NEWTSF
      ├─ Flows_UG2P
      ├─ Flows_UG2S
      ├─ Flows_UG2N
      ├─ Flows_MERS
      ├─ Flows_MERP
      └─ Flows_STOCKPILE          (All updated with your columns)

src/ui/
  └─ flow_diagram_dashboard.py    (Contains the UI you used)
```

---

## Summary

**With these UI tools, you can:**

1. ✅ **Design** entire diagrams visually
2. ✅ **Organize** components efficiently
3. ✅ **Connect** flows with flowlines
4. ✅ **Map** to Excel data
5. ✅ **Validate** all mappings
6. ✅ **Calculate** water balance
7. ✅ **Save** everything automatically
8. ✅ **Edit** components anytime
9. ✅ **Delete** with automatic cleanup
10. ✅ **Rename** across entire system

**No JSON editing required! 🎉**

---

## Next Time You Need To

### Add a component
→ Click **➕ Add Component**

### Connect components  
→ Click **✏️ Draw**

### Modify properties
→ Click component, then **✏️ Edit Node**

### Remove a component
→ Click component, then **🗑️ Delete Node**

### Save changes
→ Click **💾 Save**

### Check Excel mappings
→ Click **🔍 Validate**

### Load volume data
→ Select date, click **🔄 Load Excel**

---

**You're now ready to build complete water balance diagrams through the UI! 🚀**
