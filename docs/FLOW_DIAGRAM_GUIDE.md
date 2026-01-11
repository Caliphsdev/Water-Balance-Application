# Flow Diagram Dashboard (Current Behavior)

This guide reflects the dashboard as implemented in the Tkinter editor today. It uses manual segment drawing, JSON-backed layouts, optional Excel volume overlays, and does **not** auto-detect flow types or move flow lines when components move.

## What it does
- Manual flow lines: draw polyline segments by clicking points; arrows render from start to end. Lines stay where you drew them and do not follow components when you drag nodes.
- Component editing: add, edit, delete, and lock components (locked nodes draw with a red outline and cannot be dragged).
- Recirculation boxes: add labeled recirculation loops that sit beside a component; they can be edited or locked separately.
- Label control: flow labels render on a small white box; you can drag labels to a better position. Label font size is configurable per edge.
- Grid and scroll: grid is shown by default (20 px spacing, thicker every 100 px); canvas supports vertical/horizontal scrolling and zoom in/out buttons.
- Excel overlays: load volumes from Excel, validate sheet/column mappings, and auto-map via the Excel mapping registry helper.
- Save to JSON: saving writes the current nodes/edges to the diagram JSON. Reloading the view reads from that JSON.

## What it does not do
- No auto flow-type detection or auto-coloring based on endpoints.
- No middle-click waypoints; waypoints are explicit points you click while drawing.
- No automatic re-routing when nodes move; you must redraw or edit flow segments if a node’s position changes.

## Toolbar reference
- Flow lines: Draw, Edit, Delete.
- Recirculation: Add, Edit, Lock/Unlock.
- Components: Add Component, Edit Node, Delete Node, Lock/Unlock selection.
- Actions: Save.
- View: Zoom In, Zoom Out.
- Excel: Load Excel, Validate, Auto-Map, Mappings, Excel Manager.

## Typical workflow
1) Load: open the dashboard; it loads data/diagrams/ug2_north_decline.json and resets edge volumes/labels to "-" until Excel is loaded.
2) Move/lock components: drag nodes as needed; toggle Lock/Unlock to prevent further moves. Remember that existing flow lines do **not** follow.
3) Draw a flow line: click Draw, then click successive points to form the path. Finish on the destination point; the arrow is placed on the final segment. Choose flow type/color/volume in Edit if needed.
4) Edit a flow line: select a line in Edit, adjust flow type, color, volume/label, bidirectional flag, and label font size; save.
5) Recirculation: add a recirculation box beside a component, edit its label/size/position, or lock it.
6) Excel overlay: pick Year/Month, Load Excel to populate volumes using edge excel_mapping. Validate to check sheet/column presence; Auto-Map tries to repair missing columns using labels.
7) Save: click Save to persist nodes/edges back to JSON. Restarting reloads from that JSON.

## Data sources
- Diagram JSON: data/diagrams/ug2_north_decline.json (nodes, edges, segments, labels, locks, recirculation positions).
- Excel volumes: resolved by flow_volume_loader; mapping stored per edge in excel_mapping (sheet, column, enabled flag).

## Troubleshooting
- Flow line did not move with a component: redraw or edit the segments; lines are independent of node motion.
- Colors/types not auto-set: pick them in Edit; defaults are blue for clean, red for dirty variants, black for losses/evaporation.
- Excel validation errors: ensure the mapped sheet/column exists in the chosen workbook; use Auto-Map to repair with current labels.
