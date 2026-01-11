
# Flow Diagram - Visual Structure (Current State)

This describes the present manual-segment canvas and data-driven layout used by the Tkinter dashboard.

## Canvas and layers
- Grid is visible by default (20 px spacing; thicker every 100 px); helps hand-routing lines.
- Scrollbars support horizontal/vertical panning; zoom buttons change scale.
- Optional zone backgrounds come from the JSON (e.g., UG2 North, Merensky, Stockpile) and include their own titles.
- Nodes render as rectangles or ovals with configurable size, fill, outline, font size/weight, and lock state.

## Flows and labels
- Edges are polylines defined by stored segment coordinates. Arrowheads render on the last segment; bidirectional edges draw arrows at both ends.
- Flow lines remain independent from nodes; moving a node does not move existing edges.
- Labels sit on a white box at a calculated midpoint unless the user drags them; font size is per-edge.
- Recirculation loops render as small outlined boxes near a component; they can be locked and labeled.

## Color guidance (manual)
- Helper defaults: clean/unspecified uses blue (#3498db); dirty/effluent/runoff/return variants use red (#e74c3c); evaporation/losses use black.
- Colors are user-controlled per edge; there is no automatic endpoint-based coloring.

## Data sources and persistence
- Diagram JSON: data/diagrams/ug2_north_decline.json (nodes, edges, segments, labels, locks, recirculation positions, zone backgrounds).
- Excel overlays: edge excel_mapping defines sheet/column; volumes are populated via Flow Volume Loader when Load Excel is clicked.
- Save writes the current canvas state back to the JSON file; reload pulls from that same file.

## Interaction quick refs
- Draw flow: click Draw, then click successive points along the path, ending at the destination.
- Edit flow: pick a flow in the list, adjust type/color/volume/bidirectional/label font size, and save.
- Components: add/edit/delete; lock/unlock to control dragging.
- Recirculation: add/edit/lock loop boxes next to a component.
- Zoom/pan: use zoom buttons and scrollbars; grid remains visible for routing.
