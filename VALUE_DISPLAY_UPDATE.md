# ✨ Enhanced Mapping Editors - Now Show Flow Values!

## 🎯 What Changed

All mapping editors now display the **flow value (m³)** to help you identify which flow lines you're looking at.

### Where Values Appear

#### 1. **Edit All Mappings** - Table View
```
✅  Flow Name (27 chars)  Value (m³)    Sheet              Column
✅  guest_house → septic  350.5         Flows_UG2N         guest_house__TO__septic
⚠️  oldtsf_nt_rwd → new   -             Flows_OLDTSF       oldtsf_new_tsf__TO__oldtsf_nt_rwd
```

**How it helps:**
- Flows with actual values (like 350.5) are the active ones
- Flows with "-" are placeholder/unused flows
- Makes it easier to spot which flows matter most

#### 2. **Manual Mapper** - Step-by-Step
```
Current Flow
┌─────────────────────────────────────────────┐
│ From: guest_house                           │
│ To:   septic                                │
│ Value (m³): 350.5                           │
└─────────────────────────────────────────────┘
```

**How it helps:**
- See the actual flow value while mapping
- Quick visual confirmation you're fixing the right flow
- Helps prioritize: fix high-volume flows first

#### 3. **Edit Individual Flow** - Quick Edit Dialog
```
╔════════════════════════════════════════════════════╗
║ Flow: guest_house → septic | Value: 350.5 m³     ║
╚════════════════════════════════════════════════════╝
```

**How it helps:**
- One-line summary with value visible
- Know exactly which flow you're editing
- Saves time looking between rows

---

## 💡 Benefits

### Before (No Value)
- All flows looked the same in the list
- Couldn't tell which flows were important
- Had to remember which flows had actual data

### After (With Value)
✅ **Active flows highlighted** - See which ones matter  
✅ **Quick filtering** - Prioritize high-volume flows  
✅ **Better identification** - Know exactly which flow you're editing  
✅ **Faster corrections** - Visual confirmation before saving  

---

## 📊 Example: Identifying Important Flows

**Scenario**: You have 28 invalid flows. Which should you fix first?

**Solution**: Use Edit All Mappings
1. Look for flows with high values (e.g., 1000+, not just "-")
2. Fix those first (they impact calculations more)
3. Then handle the placeholder flows ("-" values)

**Result**: Corrected values improve water balance accuracy most!

---

## 🚀 Try It Now

1. **Launch**: `python src/main.py`
2. **Navigate**: Flow Diagram Dashboard → `[🔗 Edit Mappings]`
3. **Choose**:
   - `[Edit All Mappings]` → See table with values
   - `[Manual Mapper]` → See value in current flow panel
   - Click any flow → See value in title bar

**Look for flows with actual volume values** - those are the ones that matter most!

---

## 📝 Code Changes

**File**: `src/ui/flow_diagram_dashboard.py`

**Added value display to:**
1. Edit All Mappings table (new column: "Value (m³)")
2. Manual Mapper info panel (new field: "Value (m³)")
3. Edit Individual Flow dialog (added to title line)

**Display Logic:**
```python
volume = edge.get('volume', '-')
volume_str = str(volume) if volume not in ['-', None, ''] else '-'
volume_color = '#000' if volume not in ['-', None, ''] else '#999'
# Shows: actual number in black, "-" in gray
```

**Result**: Users can now identify and prioritize flow mappings by their actual values!
