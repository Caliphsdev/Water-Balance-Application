# Flow Diagram - Visual Guide (Current State)

This view reflects the current manual-segment editor, not the older auto-routed/auto-colored version.

## Layout
- Canvas with visible grid (20 px spacing; thicker every 100 px).
- Scrollbars for both directions; zoom in/out buttons adjust scale.
- Zone backgrounds come from the JSON (optional); titles render per zone.
- Components draw as rectangles/ovals with labels; locked nodes show a red outline.

## Flows
- Flow lines are polylines you draw point by point. They stay where you place them and do not follow components if you later move nodes.
- Arrows render on the last segment; bidirectional edges draw arrows at both ends if selected.
- Labels sit on a white box and can be dragged; font size is per-edge.
- Recirculation loops render as small outlined boxes next to a component; they can be locked.

## Colors (manual)
- Defaults from the editor helper: clean/unspecified uses blue (#3498db), dirty/effluent variants use red (#e74c3c), evaporation/losses use black.
- You can override colors per edge in the Edit dialog; there is no endpoint-based auto-coloring.

## Data bindings
- Diagram file: data/diagrams/ug2_north_decline.json (nodes, edges, segments, labels, locks, recirculation positions).
- Excel overlays: edge excel_mapping defines sheet/column; volumes load via the Flow Volume Loader when you click Load Excel.

## Quick operations
- Draw: click Draw, then click points along the desired path, ending at the target.
- Edit: choose a flow in the list, adjust type/color/volume/label font size, and save.
- Components: Add/Edit/Delete nodes; lock to prevent dragging.
- Recirculation: add/edit/lock a loop beside a component.
- Save: writes current canvas state to the diagram JSON.
