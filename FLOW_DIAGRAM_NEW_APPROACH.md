# New Simple Flow Diagram - Fresh Approach

## What Changed

I completely rewrote the flow diagram system with a **simpler, cleaner approach** that actually works.

### Old Problems Removed:
- ❌ Complex orthogonal routing that was hard to debug
- ❌ Confusing logic about when to show area vs complete diagrams
- ❌ Database dependency for component data
- ❌ Heavy use of component_positions tracking
- ❌ Confusing routing algorithms

### New Benefits:
- ✅ **Dead simple code** - ~170 lines instead of 700+
- ✅ **Direct JSON rendering** - What you see is what you get
- ✅ **Clear visual structure** - Background sections organize components
- ✅ **Easy to modify** - You can edit positions and connections directly in JSON
- ✅ **Fast rendering** - No complex calculations
- ✅ **Visual arrows** - Clear connections with flow labels
- ✅ **Well logged** - You can see exactly what's happening

## How It Works

### 1. Loads Data From JSON
```json
{
  "title": "UG2 North Decline Area",
  "nodes": [
    { "id": "guest_house", "x": 750, "y": 40, "width": 130, "height": 50, "fill": "#5d88b6" }
  ],
  "edges": [
    { "from": "reservoir", "to": "guest_house", "label": "16 105", "color": "#4b78a8" }
  ]
}
```

### 2. Draws Components
- Reads each node from JSON
- Draws rectangle or oval at specified position (x, y)
- Adds label text
- Shows component type at bottom

### 3. Draws Connections
- Draws arrow from source to destination
- Labels show flow values
- Colors show flow type (blue=clean, red=dirty, black=loss)

## Guest House & Offices NOW VISIBLE

They are defined in the JSON at:
- **Guest House**: (750, 40) - Top left area
- **Offices**: (920, 40) - Top left area, right of Guest House

Both are now guaranteed to render when diagram loads.

## How to Test

1. Close old app windows
2. Start app: `.\.venv\Scripts\python.exe src/main.py`
3. Navigate to "Flow Diagram" tab
4. Should see:
   - Clean white canvas with light gray background sections
   - All 12 components clearly labeled
   - Arrows showing water flow between components
   - Flow values labeled on each arrow

## How to Modify

### Edit Component Position
Edit `data/diagrams/ug2_north_decline.json`:
```json
{
  "id": "guest_house",
  "x": 750,      // <-- Change X position here
  "y": 40,       // <-- Change Y position here
  "width": 130,
  "height": 50,
  "fill": "#5d88b6"
}
```

### Add New Component
Add to `nodes` array:
```json
{
  "id": "new_component",
  "label": "NEW COMPONENT\n(Type)",
  "type": "consumption",
  "shape": "rect",
  "x": 600,
  "y": 100,
  "width": 120,
  "height": 50,
  "fill": "#5d88b6",
  "outline": "#2c5d8a"
}
```

### Add New Connection
Add to `edges` array:
```json
{
  "from": "reservoir",
  "to": "new_component",
  "value": 5000,
  "label": "5 000",
  "color": "#4b78a8"
}
```

Then restart the app - changes load automatically!

## Code Structure

**File**: `src/ui/flow_diagram_dashboard.py`

Methods:
- `load()` - Initializes and loads everything
- `_create_ui()` - Creates canvas with scrollbars
- `_load_diagram_data()` - Reads JSON file
- `_draw_diagram()` - Main render loop
- `_draw_background_layers()` - Organizes layout
- `_draw_node()` - Renders single component
- `_draw_edge()` - Renders connection arrow

**No more**:
- No area_configs switching
- No active_area logic
- No orthogonal routing calculations
- No hash-based offsets
- No complex positioning logic

Just: **Load JSON → Draw Components → Draw Connections**

## Next Steps

If you want to further customize:

1. **Edit component colors**: Change `"fill"` and `"outline"` values
2. **Edit component sizes**: Change `"width"` and `"height"`
3. **Edit flow colors**: Change `"color"` in edges
4. **Move things around**: Just change x, y coordinates
5. **Add more areas**: Create new JSON files in `data/diagrams/`

Everything is configurable without touching Python code!
