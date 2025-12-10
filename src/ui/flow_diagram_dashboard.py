"""
Flow Diagram Editor - Manual Segment Drawing
- Draw flow lines manually by clicking points (orthogonal segments only)
- Lines independent from components (don't move when components move)
- Click-to-draw: each click creates a segment corner
- Database-locked connections (only valid flows allowed)
"""

import json
import tkinter as tk
from tkinter import Canvas, Frame, Label, Scrollbar, messagebox, Button
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.app_logger import logger
from database.db_manager import DatabaseManager


class DetailedNetworkFlowDiagram:
    """
    Manual Segment-Based Flow Diagram Editor
    - Draw flow lines by clicking points (orthogonal 90° segments)
    - Lines are independent drawings (don't move with components)
    - Database-locked connections only
    """

    def __init__(self, parent):
        self.parent = parent
        self.canvas = None
        self.area_data = {}
        self.json_file = None
        self.db = DatabaseManager()
        
        # Node tracking
        self.selected_node = None
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.node_items = {}
        self.nodes_by_id = {}
        self.snap_to_grid = False
        self.grid_size = 20
        self.show_grid = False
        self.locked_nodes = {}  # {node_id: True/False}
        
        # Drawing mode
        self.drawing_mode = False
        self.drawing_segments = []  # [(x1,y1), (x2,y2), ...]
        self.drawing_from = None
        self.drawing_to = None
        
        # Label dragging
        self.dragging_label = False
        self.dragged_label_edge_idx = None
        self.label_items = {}  # {canvas_id: edge_index}
        
        # Valid connections from database
        self.valid_connections = set()

    def load(self):
        """Load editor"""
        for widget in self.parent.winfo_children():
            widget.destroy()

        self._load_valid_connections()
        self._create_ui()
        self._load_diagram_data()
        logger.info("✅ Manual segment flow editor loaded")

    def _load_valid_connections(self):
        """Load valid connections from database (optional reference only)"""
        try:
            # This is just for reference - we don't enforce validation
            query = '''
                SELECT DISTINCT 
                    fs.structure_code as from_code,
                    ts.structure_code as to_code
                FROM wb_flow_connections fc
                JOIN wb_structures fs ON fc.from_structure_id = fs.structure_id
                JOIN wb_structures ts ON fc.to_structure_id = ts.structure_id
            '''
            result = self.db.execute_query(query)
            self.valid_connections = set()
            for row in result:
                from_code = row.get('from_code') or row.get(0)
                to_code = row.get('to_code') or row.get(1)
                if from_code and to_code:
                    self.valid_connections.add((from_code.lower(), to_code.lower()))
            
            logger.info(f"📚 Loaded {len(self.valid_connections)} known connections (reference only)")
        except Exception as e:
            logger.info(f"ℹ️ Database reference connections not available: {e}")
            self.valid_connections = set()

    def _is_connection_valid(self, from_id, to_id):
        """Connection validation disabled - all connections allowed"""
        # You can draw any connection between any two components
        logger.info(f"✅ Drawing flow: {from_id} → {to_id}")
        return True

    def _create_ui(self):
        """Create UI"""
        controls = Frame(self.parent, bg='#2c3e50', height=120)
        controls.pack(fill='x', padx=0, pady=0)

        title = Label(controls, text='FLOW DIAGRAM - Manual Flow Line Drawing', 
                     font=('Segoe UI', 12, 'bold'), bg='#2c3e50', fg='white')
        title.pack(pady=5)

        button_frame = Frame(controls, bg='#2c3e50')
        button_frame.pack(fill='x', padx=10, pady=5)

        Button(button_frame, text='✏️ Draw Flow Line', command=self._start_drawing,
               bg='#3498db', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='� Redraw Line', command=self._start_redrawing,
               bg='#9b59b6', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='🗑️ Delete Line', command=self._delete_line,
               bg='#e74c3c', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='�💾 Save', command=self._save_to_json,
               bg='#27ae60', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='↺ Reload', command=self._reload_from_json,
               bg='#e67e22', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='🧲 Snap Grid', command=self._toggle_snap_grid,
               bg='#7f8c8d', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='📐 Show Grid', command=self._toggle_show_grid,
               bg='#95a5a6', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='⏹ Align All', command=self._align_to_grid,
               bg='#8e44ad', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='🔒 Lock/Unlock', command=self._toggle_lock_selected,
               bg='#c0392b', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)

        info = Label(controls, 
                    text='DRAG COMPONENTS to move | SELECT + "Lock/Unlock" to lock position | GRID: Snap when moving, Show for alignment',
                    font=('Segoe UI', 8), bg='#2c3e50', fg='#ecf0f1')
        info.pack(pady=2)

        info2 = Label(controls, 
                     text='🔓 Unlocked (white) = moveable | 🔒 Locked (red border) = fixed position | Grid: 20px intervals',
                     font=('Segoe UI', 7, 'italic'), bg='#2c3e50', fg='#95a5a6')
        info2.pack(pady=2)

        canvas_frame = Frame(self.parent)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.canvas = Canvas(canvas_frame, bg='#f8f9fa', highlightthickness=0, cursor='hand2')
        vscroll = Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        hscroll = Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        vscroll.grid(row=0, column=1, sticky='ns')
        hscroll.grid(row=1, column=0, sticky='ew')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas.configure(scrollregion=(0, 0, 2400, 1200))

        # Event bindings
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
        self.canvas.bind('<Button-3>', self._on_canvas_right_click)
        self.canvas.bind('<Motion>', self._on_canvas_motion)

    def _toggle_snap_grid(self):
        self.snap_to_grid = not self.snap_to_grid
        state = '✅ Enabled' if self.snap_to_grid else '❌ Disabled'
        messagebox.showinfo('Grid Snap', f'Grid snapping {state}\n\nComponents will snap to {self.grid_size}px grid when dragging.')
    
    def _toggle_show_grid(self):
        self.show_grid = not self.show_grid
        self._draw_diagram()
        state = '✅ Visible' if self.show_grid else '❌ Hidden'
        messagebox.showinfo('Grid Display', f'Grid lines {state}')
    
    def _toggle_lock_selected(self):
        if not self.selected_node:
            messagebox.showwarning('No Selection', 'Select a component first by clicking on it')
            return
        
        # Toggle lock state
        current_state = self.locked_nodes.get(self.selected_node, False)
        self.locked_nodes[self.selected_node] = not current_state
        
        new_state = '🔒 LOCKED' if self.locked_nodes[self.selected_node] else '🔓 UNLOCKED'
        print(f"[DEBUG] Toggled lock for node '{self.selected_node}': {new_state}")
        messagebox.showinfo('Lock Status', f'{self.selected_node}\n\n{new_state}')
        self._save_to_json()
        self._draw_diagram()

    def _align_to_grid(self):
        nodes = self.area_data.get('nodes', [])
        aligned_count = 0
        for node in nodes:
            # Only align unlocked nodes
            if not self.locked_nodes.get(node['id'], False):
                node['x'] = round(node['x'] / self.grid_size) * self.grid_size
                node['y'] = round(node['y'] / self.grid_size) * self.grid_size
                aligned_count += 1
        self._draw_diagram()
        locked_count = len([n for n in nodes if self.locked_nodes.get(n['id'], False)])
        messagebox.showinfo('Aligned', f'✅ {aligned_count} components aligned to grid\n🔒 {locked_count} locked components skipped')

    def _load_diagram_data(self):
        """Load diagram JSON"""
        self.json_file = Path(__file__).parent.parent.parent / 'data' / 'diagrams' / 'ug2_north_decline.json'
        
        if not self.json_file.exists():
            messagebox.showerror("Error", f"Diagram not found: {self.json_file}")
            return

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.area_data = json.load(f)
            logger.info(f"✅ Loaded: {self.area_data.get('title')}")
            self._draw_diagram()
        except Exception as e:
            logger.error(f"❌ Load error: {e}")
            messagebox.showerror("Error", f"Failed to load: {e}")

    def _draw_diagram(self):
        """Draw diagram"""
        if not self.area_data:
            return

        self.canvas.delete('all')
        self.node_items = {}
        self.nodes_by_id = {}
        self.label_items = {}  # Reset label tracking

        # Update scroll region dynamically based on diagram size (adds padding for panning)
        area_width = self.area_data.get('width', 1800)
        area_height = self.area_data.get('height', 1200)
        pad = 200
        scroll_w = area_width + pad
        scroll_h = area_height + pad
        self.canvas.configure(scrollregion=(0, 0, scroll_w, scroll_h))

        # Draw zone backgrounds (multiple areas)
        zone_bgs = self.area_data.get('zone_bg', None)
        if zone_bgs:
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    self.canvas.create_rectangle(
                        zone.get('x', 0), zone.get('y', 0),
                        zone.get('x', 0) + zone.get('width', 1800),
                        zone.get('y', 0) + zone.get('height', 420),
                        fill=zone.get('color', '#f5f6fa'), outline='', tags='zone_bg')
            else:
                # fallback for single zone_bg dict
                zone = zone_bgs
                self.canvas.create_rectangle(
                    zone.get('x', 0), zone.get('y', 0),
                    zone.get('x', 0) + zone.get('width', 1800),
                    zone.get('y', 0) + zone.get('height', 900),
                    fill=zone.get('color', '#f5f6fa'), outline='', tags='zone_bg')

        # Draw grid lines if enabled
        if self.show_grid:
            canvas_width = scroll_w
            canvas_height = scroll_h
            for x in range(0, canvas_width, self.grid_size):
                self.canvas.create_line(x, 0, x, canvas_height, fill='#e0e0e0', width=1, tags='grid')
            for y in range(0, canvas_height, self.grid_size):
                self.canvas.create_line(0, y, canvas_width, y, fill='#e0e0e0', width=1, tags='grid')
            # Thicker lines every 100px
            for x in range(0, canvas_width, 100):
                self.canvas.create_line(x, 0, x, canvas_height, fill='#bdc3c7', width=2, tags='grid')
            for y in range(0, canvas_height, 100):
                self.canvas.create_line(0, y, canvas_width, y, fill='#bdc3c7', width=2, tags='grid')

        # Title for UG2 North Decline Area
        title = self.area_data.get('title', 'Flow Diagram')
        self.canvas.create_text(50, 15, text=title, font=('Segoe UI', 14, 'bold'), 
                               fill='#2c3e50', anchor='nw')

        # Title for Merensky North Area (if present)
        merensky_title = self.area_data.get('merensky_title', None)
        if merensky_title:
            # Find the y-position of the Merensky zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            merensky_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('merensky'):
                        merensky_zone = zone
                        break
            if merensky_zone:
                y = merensky_zone.get('y', 470) + 10
            else:
                y = 480
            self.canvas.create_text(50, y, text=merensky_title, font=('Segoe UI', 14, 'bold'),
                                   fill='#2c3e50', anchor='nw')

        # Title for Stockpile Area (if present)
        stockpile_title = self.area_data.get('stockpile_title', None)
        if stockpile_title:
            # Find the y-position of the Stockpile zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            stockpile_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('stockpile'):
                        stockpile_zone = zone
                        break
            if stockpile_zone:
                y = stockpile_zone.get('y', 900) + 10
            else:
                y = 910
            self.canvas.create_text(50, y, text=stockpile_title, font=('Segoe UI', 14, 'bold'),
                                   fill='#2c3e50', anchor='nw')

        # Title for UG2 South Decline Area (if present)
        ug2south_title = self.area_data.get('ug2south_title', None)
        if ug2south_title:
            # Find the y-position of the UG2 South zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            ug2south_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('ug2 south'):
                        ug2south_zone = zone
                        break
            if ug2south_zone:
                y = ug2south_zone.get('y', 1320) + 10
            else:
                y = 1330
            self.canvas.create_text(50, y, text=ug2south_title, font=('Segoe UI', 14, 'bold'),
                                   fill='#2c3e50', anchor='nw')

        # Section labels
        self.canvas.create_text(100, 60, text='INFLOWS', font=('Segoe UI', 11, 'bold'), 
                               fill='#2980b9', anchor='center')
        self.canvas.create_text(1380, 60, text='OUTFLOWS', font=('Segoe UI', 11, 'bold'), 
                               fill='#e74c3c', anchor='center')

        # Build node lookup and load lock states
        nodes = self.area_data.get('nodes', [])
        for node in nodes:
            self.nodes_by_id[node['id']] = node
            # Load lock state from node data
            if 'locked' in node:
                self.locked_nodes[node['id']] = node['locked']

        # Draw edges (manual segments - independent from nodes)
        edges = self.area_data.get('edges', [])
        for edge in edges:
            self._draw_edge_segments(edge)

        # Draw nodes
        for node in nodes:
            self._draw_node(node)

        # Draw current drawing segments if in drawing mode
        if self.drawing_mode and len(self.drawing_segments) > 0:
            for i in range(len(self.drawing_segments) - 1):
                x1, y1 = self.drawing_segments[i]
                x2, y2 = self.drawing_segments[i + 1]
                self.canvas.create_line(x1, y1, x2, y2, fill='#3498db', width=3, 
                                       dash=(5, 3), arrow='last', arrowshape=(12, 15, 6))

        logger.info(f"Drew {len(nodes)} components and {len(edges)} flows")

    def _draw_node(self, node):
        """Draw component"""
        x, y = node['x'], node['y']
        width, height = node['width'], node['height']
        fill = node.get('fill', '#dfe6ed')
        outline = node.get('outline', '#2c3e50')
        label = node.get('label', '')
        node_id = node['id']

        # Check if locked
        is_locked = self.locked_nodes.get(node_id, False)
        is_selected = self.selected_node == node_id
        
        # Determine outline
        if is_locked:
            outline_color = '#c0392b'  # Red for locked
            outline_width = 4
        elif is_selected:
            outline_color = '#e74c3c'  # Light red for selected
            outline_width = 3
        else:
            outline_color = outline  # Normal
            outline_width = 2

        if node.get('shape') == 'oval':
            item = self.canvas.create_oval(x, y, x+width, y+height, fill=fill, 
                                          outline=outline_color, width=outline_width)
        else:
            item = self.canvas.create_rectangle(x, y, x+width, y+height, fill=fill, 
                                               outline=outline_color, width=outline_width)

        self.node_items[item] = node_id

        # Labels
        lines = label.split('\n') if label else []
        for idx, line in enumerate(lines):
            font = ('Segoe UI', 8, 'bold') if idx == 0 else ('Segoe UI', 7)
            self.canvas.create_text(x + width/2, y + 15 + (idx * 13), text=line, 
                                   font=font, fill='#000', anchor='center')

            # Only show type label for inflow/source components
            if node.get('type', '') == 'source':
                type_label = node.get('type', '').upper()
                self.canvas.create_text(x + width/2, y + height - 5, text=type_label,
                                       font=('Segoe UI', 6), fill='#7f8c8d', anchor='s')
            # Do NOT show type label for office or guest house
        
        # Add lock icon if locked
        if is_locked:
            lock_x = x + width - 12
            lock_y = y + 8
            self.canvas.create_text(lock_x, lock_y, text='🔒', font=('Segoe UI', 10),
                                   fill='#c0392b', tags=f'lock_{node_id}')

    def _draw_edge_segments(self, edge):
        """Draw flow line with dynamic snapping to component centers"""
        segments = edge.get('segments', [])
        color = edge.get('color', '#3498db')
        label = edge.get('label', '')
        from_id = edge.get('from')
        to_id = edge.get('to')
        
        # Validate components exist
        if from_id not in self.nodes_by_id or to_id not in self.nodes_by_id:
            return
        
        from_node = self.nodes_by_id[from_id]
        to_node = self.nodes_by_id[to_id]
        
        # Calculate current component center positions
        from_center_x = from_node['x'] + from_node['width'] / 2
        from_center_y = from_node['y'] + from_node['height'] / 2
        # Allow custom snap point for target component
        snap_x = edge.get('snap_x')
        snap_y = edge.get('snap_y')
        if snap_x is not None and snap_y is not None:
            to_snap_x = to_node['x'] + snap_x * to_node['width']
            to_snap_y = to_node['y'] + snap_y * to_node['height']
        else:
            to_snap_x = to_node['x'] + to_node['width'] / 2
            to_snap_y = to_node['y'] + to_node['height'] / 2

        # Calculate intersection with target component edge for arrow head
        def get_edge_intersection(x1, y1, x2, y2, node):
            # Rectangle bounds
            left = node['x']
            right = node['x'] + node['width']
            top = node['y']
            bottom = node['y'] + node['height']
            # Direction vector
            dx = x2 - x1
            dy = y2 - y1
            # Avoid division by zero
            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                return x2, y2
            # Find intersection with each side
            candidates = []
            if dx != 0:
                # Left/right sides
                t_left = (left - x1) / dx
                y_left = y1 + t_left * dy
                if 0 < t_left < 1 and top <= y_left <= bottom:
                    candidates.append((left, y_left, t_left))
                t_right = (right - x1) / dx
                y_right = y1 + t_right * dy
                if 0 < t_right < 1 and top <= y_right <= bottom:
                    candidates.append((right, y_right, t_right))
            if dy != 0:
                # Top/bottom sides
                t_top = (top - y1) / dy
                x_top = x1 + t_top * dx
                if 0 < t_top < 1 and left <= x_top <= right:
                    candidates.append((x_top, top, t_top))
                t_bottom = (bottom - y1) / dy
                x_bottom = x1 + t_bottom * dx
                if 0 < t_bottom < 1 and left <= x_bottom <= right:
                    candidates.append((x_bottom, bottom, t_bottom))
            # Pick closest intersection
            if candidates:
                candidates.sort(key=lambda c: c[2])
                return candidates[0][0], candidates[0][1]
            return x2, y2

        # For straight lines, adjust arrow head to edge
        if len(segments) == 0:
            arrow_end_x, arrow_end_y = get_edge_intersection(from_center_x, from_center_y, to_snap_x, to_snap_y, to_node)
            self.canvas.create_line(from_center_x, from_center_y, arrow_end_x, arrow_end_y,
                                   fill=color, width=1.2, arrow='last', arrowshape=(9.6, 12, 4.8))
            if label:
                mid_x = (from_center_x + arrow_end_x) / 2
                mid_y = (from_center_y + arrow_end_y) / 2
                self.canvas.create_rectangle(mid_x - 30, mid_y - 8, mid_x + 30, mid_y + 8,
                                            fill='white', outline=color, width=1, tags='flow_label')
                self.canvas.create_text(mid_x, mid_y, text=label, font=('Segoe UI', 7),
                                       fill='#2c3e50', anchor='center', tags='flow_label')
            return

        # For segmented lines, adjust last segment to edge
        if len(segments) < 2:
            return
        draw_points = []
        draw_points.append((from_center_x, from_center_y))
        for i in range(1, len(segments) - 1):
            draw_points.append(segments[i])
        # Last segment: snap to edge
        last_seg_start = draw_points[-1] if draw_points else (from_center_x, from_center_y)
        arrow_end_x, arrow_end_y = get_edge_intersection(last_seg_start[0], last_seg_start[1], to_snap_x, to_snap_y, to_node)
        draw_points.append((arrow_end_x, arrow_end_y))

        # Draw all segments using dynamic points
        for i in range(len(draw_points) - 1):
            x1, y1 = draw_points[i]
            x2, y2 = draw_points[i + 1]
            # Draw arrow on last segment only
            if i == len(draw_points) - 2:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1.2,
                                       arrow='last', arrowshape=(9.6, 12, 4.8))
            else:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1.2)

        # Draw label only once per edge, after all segments
        if label and len(draw_points) >= 2:
            label_offset = edge.get('label_offset', 0.5)
            total_segments = len(draw_points) - 1
            target_segment = int(label_offset * total_segments)
            target_segment = max(0, min(target_segment, total_segments - 1))
            segment_progress = (label_offset * total_segments) - target_segment
            x1, y1 = draw_points[target_segment]
            x2, y2 = draw_points[target_segment + 1]
            mid_x = x1 + (x2 - x1) * segment_progress
            mid_y = y1 + (y2 - y1) * segment_progress
            box_id = self.canvas.create_rectangle(mid_x - 30, mid_y - 8, mid_x + 30, mid_y + 8,
                                        fill='white', outline=color, width=1, tags='flow_label')
            text_id = self.canvas.create_text(mid_x, mid_y, text=label, font=('Segoe UI', 7),
                                   fill='#2c3e50', anchor='center', tags='flow_label')
            # Store edge index for this label
            edge_idx = self.area_data.get('edges', []).index(edge)
            self.label_items[box_id] = edge_idx
            self.label_items[text_id] = edge_idx

    def _start_redrawing(self):
        """Start redrawing an existing flow line"""
        edges = self.area_data.get('edges', [])
        if not edges:
            messagebox.showwarning("No Flows", "No flow lines to redraw")
            return
        
        # Show list of flows to choose from
        flow_list = [f"{e['from']} → {e['to']}" for e in edges]
        
        from tkinter import simpledialog
        choice = simpledialog.askinteger("Redraw Flow", 
                                        f"Choose flow to redraw (0-{len(flow_list)-1}):\n\n" + 
                                        "\n".join(f"{i}: {f}" for i, f in enumerate(flow_list)),
                                        minvalue=0, maxvalue=len(flow_list)-1)
        
        if choice is None:
            return
        
        edge = edges[choice]
        self.drawing_from = edge['from']
        self.drawing_to = edge['to']
        
        # Start with existing endpoints
        from_node = self.nodes_by_id.get(self.drawing_from)
        to_node = self.nodes_by_id.get(self.drawing_to)
        
        if not from_node or not to_node:
            messagebox.showerror("Error", "Source or destination component not found")
            return
        
        start_x = from_node['x'] + from_node['width'] / 2
        start_y = from_node['y'] + from_node['height'] / 2
        end_x = to_node['x'] + to_node['width'] / 2
        end_y = to_node['y'] + to_node['height'] / 2
        
        self.drawing_segments = [(start_x, start_y), (end_x, end_y)]
        self.drawing_mode = True
        self.canvas.config(cursor='crosshair')
        
        logger.info(f"🔄 Redrawing: {self.drawing_from} → {self.drawing_to}")
        messagebox.showinfo("Redraw Mode", 
                           "Click points to reshape the flow path\n"
                           "Click TO component when done (or right-click to cancel)")

    def _delete_line(self):
        """Delete an existing flow line"""
        edges = self.area_data.get('edges', [])
        if not edges:
            messagebox.showwarning("No Flows", "No flow lines to delete")
            return
        
        flow_list = [f"{e['from']} → {e['to']}" for e in edges]
        
        from tkinter import simpledialog
        choice = simpledialog.askinteger("Delete Flow", 
                                        f"Choose flow to DELETE (0-{len(flow_list)-1}):\n\n" + 
                                        "\n".join(f"{i}: {f}" for i, f in enumerate(flow_list)),
                                        minvalue=0, maxvalue=len(flow_list)-1)
        
        if choice is None:
            return
        
        edge = edges[choice]
        if messagebox.askyesno("Confirm Delete", f"Delete: {edge['from']} → {edge['to']}?"):
            edges.pop(choice)
            self._draw_diagram()
            logger.info(f"🗑️ Deleted flow: {edge['from']} → {edge['to']}")
            messagebox.showinfo("Deleted", "Flow line removed")

    def _start_drawing(self):
        """Start manual flow line drawing"""
        self.drawing_mode = True
        self.drawing_segments = []
        self.drawing_from = None
        self.drawing_to = None
        self.canvas.config(cursor='crosshair')
        messagebox.showinfo("Draw Mode", 
                           "1. Click FROM component\n"
                           "2. Click points to draw path (auto-snaps to 90°)\n"
                           "3. Click TO component to finish\n"
                           "Right-click to cancel")

    def _on_canvas_click(self, event):
        """Handle click"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Drawing mode
        if self.drawing_mode:
            # Check if clicked on node
            clicked_node = self._get_node_at(canvas_x, canvas_y)
            if self.drawing_from is None:
                # First click - select FROM component
                if clicked_node:
                    self.drawing_from = clicked_node
                    node = self.nodes_by_id[clicked_node]
                    start_x = node['x'] + node['width'] / 2
                    start_y = node['y'] + node['height'] / 2
                    self.drawing_segments = [(start_x, start_y)]
                    messagebox.showinfo("From Selected", f"Drawing from: {clicked_node}\nNow click points to draw path")
                else:
                    messagebox.showwarning("Invalid", "Click on a component to start")
            elif clicked_node and clicked_node != self.drawing_from:
                # Clicked on a component - finish drawing
                node = self.nodes_by_id[clicked_node]
                # Snap to exact click location on target node
                snap_x = (canvas_x - node['x']) / node['width'] if node['width'] else 0.5
                snap_y = (canvas_y - node['y']) / node['height'] if node['height'] else 0.5
                self.drawing_segments.append((canvas_x, canvas_y))
                # Create edge
                self._finish_drawing(self.drawing_from, clicked_node, snap_x=snap_x, snap_y=snap_y)
            else:
                # Clicked on canvas - add segment point (snap to 90°)
                if len(self.drawing_segments) > 0:
                    last_x, last_y = self.drawing_segments[-1]
                    # Snap to 90° - lock to horizontal or vertical
                    dx = abs(canvas_x - last_x)
                    dy = abs(canvas_y - last_y)
                    if dx > dy:
                        # Horizontal
                        self.drawing_segments.append((canvas_x, last_y))
                    else:
                        # Vertical
                        self.drawing_segments.append((last_x, canvas_y))
                    self._draw_diagram()
            return

        # Check if clicked on a flow label
        clicked_items = self.canvas.find_overlapping(canvas_x - 2, canvas_y - 2, canvas_x + 2, canvas_y + 2)
        for item in clicked_items:
            if item in self.label_items:
                self.dragging_label = True
                self.dragged_label_edge_idx = self.label_items[item]
                self.drag_start_x = canvas_x
                self.drag_start_y = canvas_y
                logger.info(f"📝 Dragging label for edge {self.dragged_label_edge_idx}")
                return

        # Normal mode - drag components
        clicked_node = self._get_node_at(canvas_x, canvas_y)
        if clicked_node:
            self.selected_node = clicked_node
            self.dragging = True
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self._draw_diagram()

    def _on_canvas_drag(self, event):
        """Handle drag"""
        if self.drawing_mode:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Label dragging
        if self.dragging_label and self.dragged_label_edge_idx is not None:
            edges = self.area_data.get('edges', [])
            if self.dragged_label_edge_idx < len(edges):
                edge = edges[self.dragged_label_edge_idx]
                
                # Calculate new label offset along the flow path
                from_id = edge.get('from')
                to_id = edge.get('to')
                
                if from_id in self.nodes_by_id and to_id in self.nodes_by_id:
                    # Build path points
                    from_node = self.nodes_by_id[from_id]
                    to_node = self.nodes_by_id[to_id]
                    from_x = from_node['x'] + from_node['width'] / 2
                    from_y = from_node['y'] + from_node['height'] / 2
                    to_x = to_node['x'] + to_node['width'] / 2
                    to_y = to_node['y'] + to_node['height'] / 2
                    
                    segments = edge.get('segments', [])
                    if len(segments) >= 2:
                        path_points = [(from_x, from_y)]
                        for i in range(1, len(segments) - 1):
                            path_points.append(segments[i])
                        path_points.append((to_x, to_y))
                    else:
                        path_points = [(from_x, from_y), (to_x, to_y)]
                    
                    # Find closest point on path to mouse
                    min_dist = float('inf')
                    best_offset = 0.5
                    
                    for i in range(len(path_points) - 1):
                        x1, y1 = path_points[i]
                        x2, y2 = path_points[i + 1]
                        
                        # Find closest point on this segment
                        segment_len = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                        if segment_len > 0:
                            t = max(0, min(1, ((canvas_x - x1) * (x2 - x1) + (canvas_y - y1) * (y2 - y1)) / segment_len**2))
                            closest_x = x1 + t * (x2 - x1)
                            closest_y = y1 + t * (y2 - y1)
                            dist = ((canvas_x - closest_x)**2 + (canvas_y - closest_y)**2)**0.5
                            
                            if dist < min_dist:
                                min_dist = dist
                                # Calculate offset along entire path (0.0 to 1.0)
                                best_offset = (i + t) / (len(path_points) - 1)
                    
                    # Update edge with new label offset (only if changed significantly)
                    if abs(edge.get('label_offset', 0.5) - best_offset) > 0.01:
                        edge['label_offset'] = best_offset
                        self._draw_diagram()
            return
        
        # Component dragging
        if not self.dragging or not self.selected_node:
            return
        
        # Check if node is locked
        print(f"[DEBUG] Drag attempt: selected_node='{self.selected_node}', locked={self.locked_nodes.get(self.selected_node, False)}")
        if self.locked_nodes.get(self.selected_node, False):
            print(f"[DEBUG] Node '{self.selected_node}' is locked. Drag ignored.")
            return  # Don't move locked nodes
        canvas_x = self.canvas.canvasx(event.x)

        dx = canvas_x - self.drag_start_x
        dy = canvas_y - self.drag_start_y

        node = self.nodes_by_id[self.selected_node]
        node['x'] += dx
        node['y'] += dy

        if self.snap_to_grid:
            node['x'] = round(node['x'] / self.grid_size) * self.grid_size
            node['y'] = round(node['y'] / self.grid_size) * self.grid_size

        self.drag_start_x = canvas_x
        self.drag_start_y = canvas_y
        self._draw_diagram()

    def _on_canvas_release(self, event):
        """Handle release"""
        self.dragging = False
        self.dragging_label = False
        self.dragged_label_edge_idx = None

    def _on_canvas_right_click(self, event):
        """Handle right-click - cancel drawing or delete"""
        if self.drawing_mode:
            self.drawing_mode = False
            self.drawing_segments = []
            self.drawing_from = None
            self.drawing_to = None
            self.canvas.config(cursor='hand2')
            messagebox.showinfo("Cancelled", "Drawing cancelled")
            return

        # Delete node
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        clicked_node = self._get_node_at(canvas_x, canvas_y)
        
        if clicked_node:
            if messagebox.askyesno("Delete", f"Delete component '{clicked_node}'?"):
                nodes = self.area_data.get('nodes', [])
                edges = self.area_data.get('edges', [])
                self.area_data['nodes'] = [n for n in nodes if n['id'] != clicked_node]
                self.area_data['edges'] = [e for e in edges 
                                          if e['from'] != clicked_node and e['to'] != clicked_node]
                self._draw_diagram()

    def _on_canvas_motion(self, event):
        """Handle mouse motion - show preview line when drawing"""
        if not self.drawing_mode or len(self.drawing_segments) == 0:
            return

        # Only redraw if we have a preview line tag
        if hasattr(self, '_preview_line_id') and self._preview_line_id:
            self.canvas.delete(self._preview_line_id)

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        last_x, last_y = self.drawing_segments[-1]
        
        # Snap preview to 90°
        dx = abs(canvas_x - last_x)
        dy = abs(canvas_y - last_y)
        
        if dx > dy:
            # Horizontal preview
            self._preview_line_id = self.canvas.create_line(last_x, last_y, canvas_x, last_y, 
                                   fill='#95a5a6', width=2, dash=(3, 3), tags='preview')
        else:
            # Vertical preview
            self._preview_line_id = self.canvas.create_line(last_x, last_y, last_x, canvas_y, 
                                   fill='#95a5a6', width=2, dash=(3, 3), tags='preview')

    def _finish_drawing(self, from_id, to_id, snap_x=0.5, snap_y=0.5):
        """Finish drawing and create or update edge"""
        edges = self.area_data.get('edges', [])
        
        # Ask for flow type and volume FIRST (before checking for existing flows)
        from tkinter import simpledialog

        flow_type = simpledialog.askstring(
            "Flow Type",
            f"Flow: {from_id} → {to_id}\n\n"
            "Choose flow type (examples):\n"
            "- clean (potable/treated water)\n"
            "- dirty (wastewater)\n"
            "- dewatering (dirty water, mine water)\n"
            "- ug_return (underground return water)\n"
            "- process_dirty (process plant dirty water)\n"
            "- stormwater (rainfall runoff)\n"
            "- recirculation (internal return)\n"
            "- evaporation (loss to air, black line)",
            initialvalue="clean"
        )

        if not flow_type:
            messagebox.showwarning("Cancelled", "Flow type required. Drawing cancelled.")
            self.drawing_mode = False
            self.drawing_segments = []
            self.drawing_from = None
            self.canvas.config(cursor='hand2')
            self._draw_diagram()
            return

        volume = simpledialog.askfloat(
            "Flow Volume",
            f"Flow: {from_id} → {to_id}\n"
            f"Type: {flow_type}\n\n"
            "Enter flow volume (m³/month):",
            minvalue=0
        )

        if volume is None:
            messagebox.showwarning("Cancelled", "Volume required. Drawing cancelled.")
            self.drawing_mode = False
            self.drawing_segments = []
            self.drawing_from = None
            self.canvas.config(cursor='hand2')
            self._draw_diagram()
            return

        # NOW check if we already have this EXACT flow (same from, to, AND flow_type)
        existing_idx = None
        for idx, edge in enumerate(edges):
            if (edge['from'] == from_id and 
                edge['to'] == to_id and 
                edge.get('flow_type', '').lower() == flow_type.lower()):
                existing_idx = idx
                break

        # Snap_x and snap_y are now passed in from the click location on the target node

        # Determine color based on flow type
        color_map = {
            'clean': '#4b78a8',         # Blue
            'dirty': '#e74c3c',         # Red
            'dewatering': '#e74c3c',    # Red
            'ug_return': '#e74c3c',     # Red
            'process_dirty': '#e74c3c', # Red
            'stormwater': '#e74c3c',    # Red
            'recirculation': '#9b59b6', # Purple
            'evaporation': '#000000'    # Black
        }
        color = color_map.get(flow_type.lower(), '#3498db')

        # Format label with commas
        label = f"{volume:,.0f}"

        if existing_idx is not None:
            # Update existing flow
            edges[existing_idx]['segments'] = self.drawing_segments[:]
            edges[existing_idx]['flow_type'] = flow_type
            edges[existing_idx]['volume'] = volume
            edges[existing_idx]['color'] = color
            edges[existing_idx]['label'] = label
            edges[existing_idx]['snap_x'] = snap_x
            edges[existing_idx]['snap_y'] = snap_y
            logger.info(f"✏️ Updated flow: {from_id} → {to_id} ({flow_type}, {label} m³)")
        else:
            # Create new edge
            new_edge = {
                'from': from_id,
                'to': to_id,
                'segments': self.drawing_segments[:],
                'flow_type': flow_type,
                'volume': volume,
                'color': color,
                'label': label,
                'snap_x': snap_x,
                'snap_y': snap_y
            }
            edges.append(new_edge)
            logger.info(f"✅ Created flow: {from_id} → {to_id} ({flow_type}, {label} m³)")

        self.area_data['edges'] = edges
        self.drawing_mode = False
        self.drawing_segments = []
        self.drawing_from = None
        self.canvas.config(cursor='hand2')
        
        self._draw_diagram()
        messagebox.showinfo("Success", f"Flow saved: {from_id} → {to_id}\n{flow_type.title()}: {label} m³")

    def _get_node_at(self, x, y):
        """Get node at position"""
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            if item in self.node_items:
                return self.node_items[item]
        return None

    def _save_to_json(self):
        """Save to JSON"""
        try:
            # Save lock states to node data
            for node in self.area_data.get('nodes', []):
                node['locked'] = self.locked_nodes.get(node['id'], False)
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.area_data, f, indent=2, ensure_ascii=False)
            logger.info("✅ Saved diagram")
            messagebox.showinfo("Saved", "All changes saved!")
        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            messagebox.showerror("Error", f"Failed to save: {e}")

    def _reload_from_json(self):
        """Reload from file"""
        if messagebox.askyesno("Reload", "Discard unsaved changes?"):
            self._load_diagram_data()
            messagebox.showinfo("Reloaded", "Reloaded from file")


# For compatibility
FlowDiagramDashboard = DetailedNetworkFlowDiagram
