# Interactive Flow Diagram Editor - User Guide

## 🎯 What You Can Do Now

You now have a **fully interactive flow diagram editor** inside the app where you can:

### 1. **Drag Components** ↔️
- Click and drag any component to move it anywhere
- Position them exactly how you want
- Changes are live - no need to restart

### 2. **Create Connections** 🔗
- Click "🔗 Connect Components" button
- Click first component (it will highlight in red)
- Click second component to connect them
- Enter the flow value (in m³)
- Connection appears with arrow and value label

### 3. **Delete Components** 🗑️
- Right-click on any component
- Click "Yes" to delete it
- All its connections are deleted too

### 4. **Save Everything** 💾
- Click "💾 Save Changes" button
- All positions, connections, values saved to JSON
- Changes persist when you close and reopen the app

### 5. **Reload from File** ↺
- Click "↺ Reload from File" button
- Discard all unsaved changes
- Start fresh from saved file

---

## 📋 Step-by-Step Tutorial

### Moving a Component

1. In the Flow Diagram tab, locate "Guest House" component
2. Click and drag it to a new position
3. Release mouse - it stays there
4. Repeat for any other component
5. Click "Save Changes" when done

### Creating a New Connection

1. Click "🔗 Connect Components" button
2. Message appears: "Click on a component to start"
3. Click "Reservoir" (it highlights red) - message says "Now click target component"
4. Click another component like "Septic Tank"
5. Enter flow value in popup (e.g., `3000`)
6. Connection created with arrow showing the flow
7. Click "Save Changes" to keep it

### Deleting a Component

1. Right-click on the component you want to delete
2. Confirmation dialog: "Delete component 'guest_house'?"
3. Click "Yes" to delete
4. Component and all its connections removed
5. Click "Save Changes" to keep the change

### Rearranging the Entire Diagram

1. Move all components to new positions
2. Create new connections as needed
3. Delete old connections by removing components
4. Click "Save Changes" when satisfied

---

## 🎨 What You'll See

```
┌─────────────────────────────────────────────────────────────┐
│ INTERACTIVE FLOW DIAGRAM EDITOR                             │
│ [🔗 Connect] [💾 Save] [↺ Reload]                          │
│ Instructions: Drag components | Right-click to delete       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SOURCES        TREATMENT      STORAGE       DISTRIBUTION   │
│  ┌─────────┐    ┌────────┐                   ┌─────────┐   │
│  │Borehole ├────→Softening├──→ Reservoir ────→Guest    │   │
│  └─────────┘    └────────┘    (Draggable)    │House    │   │
│                                 (SELECTED)    └─────────┘   │
│                                                               │
│  Drag arrow shows component is selected                      │
│  Right-click any component to delete it                      │
│  Connections show flow values with arrows                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Example

### Scenario: Reorganize diagram to be left-to-right

1. **Setup Connection Mode**: Click "🔗 Connect Components"
2. **Delete old arrangement**: Right-click each component, delete
3. **Start fresh**: Now you have just the initial components
4. **Position components** left to right horizontally
5. **Create new connections** in the order you want
6. **Save** - all changes persisted

OR

### Scenario: Move everything to the left side

1. Start dragging components
2. As you drag, all connected arrows move with them
3. Reposition until satisfied
4. Click "Save Changes"
5. Done! Changes are permanent

---

## ⚙️ How It Works

### Behind the Scenes

All your changes are stored in:
```
data/diagrams/ug2_north_decline.json
```

When you:
- **Drag** a component → its `x`, `y` coordinates change
- **Create connection** → new entry added to `edges` array
- **Delete component** → removed from `nodes` array
- **Save** → all changes written to JSON file

### What Gets Saved

```json
{
  "nodes": [
    {
      "id": "guest_house",
      "x": 800,        // ← Updated when you drag
      "y": 150,        // ← Updated when you drag
      "width": 130,
      "height": 50,
      "fill": "#5d88b6"
    }
  ],
  "edges": [
    {
      "from": "reservoir",
      "to": "guest_house",
      "value": 16105,  // ← You entered this
      "label": "16,105",
      "color": "#4b78a8"
    }
  ]
}
```

---

## 💡 Tips & Tricks

### Make Better Layouts

1. **Group by type**: Put all sources on left, storage in middle, consumption on right
2. **Avoid crossing lines**: Position components so arrows don't cross
3. **Line up vertically**: Align components at same height when possible
4. **Space them out**: Give components room so text doesn't overlap

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Component won't move | Make sure you're clicking on it, then drag |
| Connection didn't create | Make sure you're in Connect mode (blue button) |
| Changes disappeared | You didn't click "Save Changes" button |
| Can't delete component | Right-click it, then click Yes on confirmation |
| Component labels overlap | Drag one of them to a new position |

### Keyboard Shortcuts

Currently: None, but you can:
- Use mouse wheel to scroll
- Use scrollbars to navigate
- Click any component to interact with it

---

## 📁 Files Involved

- **Editor code**: `src/ui/flow_diagram_dashboard.py`
- **Diagram data**: `data/diagrams/ug2_north_decline.json`
- **Main app**: `src/ui/main_window.py` (calls the editor)

---

## 🚀 What's Next?

You can:

1. **Add new components**: Manually edit JSON file and add new nodes
2. **Create new diagrams**: Create `new_area.json` in `data/diagrams/` folder
3. **Export diagrams**: Save as image (can be added later)
4. **Import data**: Load real flow values from database (can be added later)

---

## ✅ You Now Have Full Control!

- **No more fixed layouts** - arrange however you want
- **No coding needed** - everything visual
- **Changes persist** - saved automatically
- **Easy to experiment** - reload from file anytime
- **Completely flexible** - create any diagram structure

Just click, drag, connect, and save! 🎯
