# Quick Reference: Add Components in UI

## TL;DR - 3 Steps

```
1. Click ➕ Add Component button
2. Fill form with component details
3. Click ✅ Create → See it in diagram instantly
```

---

## Component Types (Pick One)

```
source          Boreholes, water intake
process         Processing units, operations
storage         Tanks, reservoirs, containment
consumption     Offices, end users
building        Office buildings
treatment       Sewage treatment, water treatment
plant           Concentrator plants
tsf             Tailings storage facilities
reservoir       Water storage tanks
loss            Evaporation, losses, waste
discharge       Environmental discharge
```

---

## Common Colors (Hex Codes)

```
#4b78a8  Blue water    (clean flows)
#f39c12  Orange       (treatment/process)
#e74c3c  Red          (dirty/waste)
#148f77  Teal         (underground)
#5dade2  Light blue   (buildings)
#95a5a6  Gray         (plants/systems)
#f9a825  Gold         (TSF/storage)
#27ae60  Green        (success/new)
#2c3e50  Dark gray    (outlines)
```

---

## Shape Options

```
rect    Rectangle (default) ▭
oval    Circle/Oval        ◯
diamond Diamond shape      ◇
```

---

## ID Naming Convention

```
Format: [area]_[description]_[type]

Examples:
  oldtsf_treatment_tank
  ug2plant_softening_plant
  stockpile_processing_unit
  newtsf_collection_tank
  
Rules:
  • Use lowercase
  • Use underscores (not spaces)
  • Must be unique
  • Keep it descriptive
```

---

## Button Locations

### Add Component
```
🔧 COMPONENTS: [➕ Add Component] ← Click here
```

### After Creating

```
✏️ Edit Node      → Modify properties
🗑️ Delete Node    → Remove component
🔒 Lock/Unlock    → Prevent moves
💾 Save           → Persist changes
```

---

## After Creating Component

### Add Flowlines
1. Click **✏️ Draw** button
2. Click source component
3. Click target component
4. Edit line properties if needed

### Add Excel Data
1. Open Excel template
2. Go to appropriate Flows sheet
3. Add column: `[COMPONENT_FROM] → [COMPONENT_TO]`
4. Add volume data below

### Edit Component
1. Click component on diagram
2. Click **✏️ Edit Node**
3. Change label, size, colors, etc.
4. Click **Save Changes**

---

## Validation Rules

✓ Component ID is **required**  
✓ Component ID must be **unique**  
✓ Position X/Y within **0-2000 / 0-3500**  
✓ Width **40-400 pixels**  
✓ Height **20-200 pixels**  
✓ Colors **hex format** (#rrggbb)  

---

## Keyboard Tips

| Key | Action |
|-----|--------|
| Tab | Navigate to next field |
| Enter | Submit form |
| Esc | Cancel (doesn't close dialog - click button) |
| Arrow keys | Adjust spinbox values |

---

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Component not visible | Adjust Position X/Y (try 500, 500) |
| Can't find component | Zoom out and pan around |
| ID says duplicate | Use different ID (check JSON for existing) |
| Component is off-screen | Use zoom buttons to find it |
| Changes disappeared | Click **💾 Save** before closing |
| Component won't connect | Use **Lock/Unlock** then redraw |

---

## Complete Checklist

Creating a new complete component:

```
☐ Click ➕ Add Component
☐ Enter unique Component ID
☐ Enter descriptive Label
☐ Set Position X, Y
☐ Set Width, Height
☐ Choose Type (source, process, storage, etc.)
☐ Choose Shape (rect, oval, diamond)
☐ Set Fill Color (hex code)
☐ Set Outline Color (hex code)
☐ Click ✅ Create
☐ Select component on diagram
☐ Click ✏️ Edit (if adjustments needed)
☐ Draw flowlines to it (✏️ Draw button)
☐ Add Excel columns for those flowlines
☐ Add volume data in Excel
☐ Click 💾 Save
☐ Test: Run app and navigate to Flow Diagram
```

---

## Time Saver: Recommended Defaults

```
Position:  Start at 500, 500 (adjust as needed)
Width:     120 pixels (good default)
Height:    40 pixels (compact)
Type:      process (most versatile)
Shape:     rect (standard)
Fill:      #3498db (blue)
Outline:   #2c3e50 (dark gray)
```

---

## Pro Tips

💡 **Use similar colors for related components**
   - All treatment plants: Orange
   - All storage: Blue
   - All losses: White

💡 **Position logically**
   - Left side: Sources (inputs)
   - Center: Processing/storage
   - Right side: Losses/discharge

💡 **Lock components after positioning**
   - Prevents accidental movement
   - Keeps diagram organized

💡 **Create flowlines immediately**
   - Don't wait to connect components
   - Easier to track data flow

💡 **Test in Excel first**
   - Add test data column
   - Verify it loads in app
   - Then add real data

---

## When You're Done

```
✅ Component visible on diagram
✅ Flowlines connected to it
✅ Excel columns mapped
✅ Volume data entered
✅ Changes saved to JSON
✅ Ready for calculations!
```

---

**That's it! You're now equipped to add components through the UI. Happy building! 🎉**
