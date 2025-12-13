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
        self.edge_to_label_items = {}  # {edge_idx: [box_id, text_id]}
        
        # Redraw state (track which edge is being redrawn)
        self.redraw_edge_index = None
        
        # Snap to component
        self.snap_distance = 30  # pixels to snap
        self.snap_anchor_points = {}  # {node_id: [anchor_points]}
        self.hovered_anchor = None  # Currently hovered anchor point
        
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
        
        Button(button_frame, text='📏 Straighten', command=self._straighten_line,
               bg='#16a085', fg='white', font=('Segoe UI', 9), padx=10).pack(side='left', padx=5)
        
        Button(button_frame, text='💾 Save', command=self._save_to_json,
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

    def _find_nearest_anchor(self, node_id, click_x, click_y):
        """Find nearest anchor point on component, snap if within snap_distance"""
        if node_id not in self.snap_anchor_points:
            return None
        
        anchors = self.snap_anchor_points[node_id]
        min_dist = float('inf')
        best_anchor = None
        
        for anchor_name, (ax, ay) in anchors.items():
            dist = ((click_x - ax)**2 + (click_y - ay)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                best_anchor = (ax, ay)
        
        # Only snap if within snap_distance
        if min_dist <= self.snap_distance:
            logger.debug(f"🔧 Snapped to anchor: distance={min_dist:.1f}px")
            return best_anchor
        
        return None

    def _get_node_area(self, node_id):
        """Determine which area a node belongs to based on its y-position"""
        if node_id not in self.nodes_by_id:
            return "Unknown"
        
        node = self.nodes_by_id[node_id]
        node_y = node['y']
        
        # Check zone backgrounds to determine area
        zone_bgs = self.area_data.get('zone_bg', [])
        for zone in zone_bgs:
            zone_y = zone.get('y', 0)
            zone_height = zone.get('height', 0)
            if zone_y <= node_y < (zone_y + zone_height):
                return zone.get('name', 'Unknown')
        
        # Fallback: check node_id prefix patterns
        node_id_lower = node_id.lower()
        if 'ug2n' in node_id_lower or node_id_lower.startswith('ug2_'):
            return "UG2 North Decline Area"
        elif 'meren' in node_id_lower and 'north' in node_id_lower:
            return "Merensky North Area"
        elif 'stockpile' in node_id_lower or 'spcd' in node_id_lower:
            return "Stockpile Area"
        elif 'ug2s' in node_id_lower or 'ug2_south' in node_id_lower:
            return "UG2 South Decline Area"
        elif 'meren' in node_id_lower or 'mers' in node_id_lower:
            return "Merensky South Area"
        elif 'oldtsf' in node_id_lower or 'old_tsf' in node_id_lower:
            return "Old TSF Area"
        
        return "Other"

    def _format_node_name(self, node_id):
        """Format node name for display - remove prefix and make readable"""
        if node_id not in self.nodes_by_id:
            return node_id
        
        node = self.nodes_by_id[node_id]
        label = node.get('label', node_id)
        
        # Replace newlines with spaces for better display
        label = label.replace('\n', ' ')
        
        return label

    def _update_connected_edges(self, node_id, dx, dy):
        """Update all edges connected to a moved component"""
        edges = self.area_data.get('edges', [])
        
        for edge in edges:
            updated = False
            segments = edge.get('segments', [])
            
            if not segments or len(segments) < 2:
                continue
            
            # Update first point if this is the FROM node
            if edge.get('from') == node_id:
                old_x, old_y = segments[0]
                segments[0] = [old_x + dx, old_y + dy]
                updated = True
            
            # Update last point if this is the TO node
            if edge.get('to') == node_id:
                old_x, old_y = segments[-1]
                segments[-1] = [old_x + dx, old_y + dy]
                updated = True
            
            if updated:
                logger.debug(f"📌 Updated edge {edge.get('from')} → {edge.get('to')}")

    def _straighten_edge(self, edge_idx):
        """Straighten a flow line by creating direct path from start to end"""
        edges = self.area_data.get('edges', [])
        if edge_idx >= len(edges):
            return
        
        edge = edges[edge_idx]
        segments = edge.get('segments', [])
        
        if len(segments) < 2:
            return
        
        # Keep only first and last points
        start_point = segments[0]
        end_point = segments[-1]
        
        # Create straight line
        edge['segments'] = [start_point, end_point]
        
        logger.info(f"📏 Straightened edge {edge.get('from')} → {edge.get('to')}")
        self._draw_diagram()
        messagebox.showinfo("Straightened", f"Flow line from {edge.get('from')} to {edge.get('to')} is now straight")

    def _draw_snap_anchors_in_drawing_mode(self):
        """Draw anchor points for all components when in drawing mode"""
        if not self.drawing_mode:
            return
        
        for node_id, anchors in self.snap_anchor_points.items():
            # Draw anchor points as small circles
            for anchor_name, (ax, ay) in anchors.items():
                # Skip center anchor to reduce clutter
                if anchor_name == 'center':
                    continue
                
                radius = 4
                # Check if this is the hovered anchor
                is_hovered = (anchor_name == self.hovered_anchor.get('name') and 
                             self.hovered_anchor.get('node_id') == node_id) if self.hovered_anchor else False
                
                color = '#f39c12' if is_hovered else '#95a5a6'  # Orange if hovered, gray otherwise
                self.canvas.create_oval(ax-radius, ay-radius, ax+radius, ay+radius, 
                                       fill=color, outline='#2c3e50', width=1)

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
        self.label_items = {}  # Reset label tracking (canvas_item_id -> edge_idx)
        self.edge_to_label_items = {}  # Reverse mapping (edge_idx -> [box_id, text_id])

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

        # Title for Merensky South Area (if present)
        merenskysouth_title = self.area_data.get('merenskysouth_title', None)
        if merenskysouth_title:
            # Find the y-position of the Merensky South zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            merenskysouth_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('merensky south'):
                        merenskysouth_zone = zone
                        break
            if merenskysouth_zone:
                y = merenskysouth_zone.get('y', 1640) + 10
            else:
                y = 1650
            self.canvas.create_text(50, y, text=merenskysouth_title, font=('Segoe UI', 14, 'bold'),
                                   fill='#2c3e50', anchor='nw')

        # Title for Old TSF Area (if present)
        oldtsf_title = self.area_data.get('oldtsf_title', None)
        if oldtsf_title:
            # Find the y-position of the Old TSF zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            oldtsf_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('old tsf'):
                        oldtsf_zone = zone
                        break
            if oldtsf_zone:
                y = oldtsf_zone.get('y', 2070) + 10
            else:
                y = 2080
            self.canvas.create_text(50, y, text=oldtsf_title, font=('Segoe UI', 14, 'bold'),
                                   fill='#2c3e50', anchor='nw')

        # Title for UG2 Plant Area (if present)
        ug2plant_title = self.area_data.get('ug2plant_title', None)
        if ug2plant_title:
            # Find the y-position of the UG2 Plant zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            ug2plant_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('ug2 plant'):
                        ug2plant_zone = zone
                        break
            if ug2plant_zone:
                y = ug2plant_zone.get('y', 2650) + 10
            else:
                y = 2660
            self.canvas.create_text(50, y, text=ug2plant_title, font=('Segoe UI', 14, 'bold'),
                                   fill='#2c3e50', anchor='nw')

        # Title for Merensky Plant Area (if present)
        merplant_title = self.area_data.get('merplant_title', None)
        if merplant_title:
            # Find the y-position of the Merensky Plant zone background
            zone_bgs = self.area_data.get('zone_bg', [])
            merplant_zone = None
            if isinstance(zone_bgs, list):
                for zone in zone_bgs:
                    if zone.get('name', '').lower().startswith('merensky plant'):
                        merplant_zone = zone
                        break
            if merplant_zone:
                y = merplant_zone.get('y', 3230) + 10
            else:
                y = 3240
            self.canvas.create_text(50, y, text=merplant_title, font=('Segoe UI', 14, 'bold'),
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
        for idx, edge in enumerate(edges):
            self._draw_edge_segments(edge, idx)

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
        
        # Draw snap anchor points when in drawing mode
        self._draw_snap_anchors_in_drawing_mode()

        logger.info(f"Drew {len(nodes)} components and {len(edges)} flows")
        logger.debug(f"Tracking {len(self.label_items)} label items: {self.label_items}")

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

        # Calculate and store anchor points for snap-to functionality
        # Increased density: quarters along each side + corners + midpoints + center
        cx = x + width / 2
        cy = y + height / 2
        qx1 = x + width * 0.25
        qx3 = x + width * 0.75
        qy1 = y + height * 0.25
        qy3 = y + height * 0.75

        anchors = {
            'center': (cx, cy),
            # Top edge
            'top_left': (x, y),
            'top_q1': (qx1, y),
            'top': (cx, y),
            'top_q3': (qx3, y),
            'top_right': (x + width, y),
            # Bottom edge
            'bottom_left': (x, y + height),
            'bottom_q1': (qx1, y + height),
            'bottom': (cx, y + height),
            'bottom_q3': (qx3, y + height),
            'bottom_right': (x + width, y + height),
            # Left edge
            'left_top_q1': (x, qy1),
            'left': (x, cy),
            'left_bottom_q3': (x, qy3),
            # Right edge
            'right_top_q1': (x + width, qy1),
            'right': (x + width, cy),
            'right_bottom_q3': (x + width, qy3)
        }
        self.snap_anchor_points[node_id] = anchors

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

    def _get_edge_connection_point(self, node, click_x, click_y):
        """Get connection point from user's exact click location on node.
        
        Args:
            node: Node dictionary with x, y, width, height
            click_x: X coordinate where user clicked
            click_y: Y coordinate where user clicked
            
        Returns:
            Tuple of (x, y) coordinates at click location
        """
        # Return exact click point - user has full control
        return click_x, click_y

    def _draw_edge_segments(self, edge, edge_idx):
        """Draw flow line with manual control and proper arrow placement"""
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
        
        # Use stored segment points directly - full manual control
        if len(segments) >= 2:
            # User-defined start and end points
            from_x, from_y = segments[0]
            to_x, to_y = segments[-1]
        else:
            # Fallback to center if no segments stored
            from_x = from_node['x'] + from_node['width'] / 2
            from_y = from_node['y'] + from_node['height'] / 2
            to_x = to_node['x'] + to_node['width'] / 2
            to_y = to_node['y'] + to_node['height'] / 2

        # Calculate intersection with component edge for precise arrow head placement
        def get_edge_intersection(x1, y1, x2, y2, node):
            """Calculate where line intersects component boundary"""
            # Rectangle bounds
            left = node['x']
            right = node['x'] + node['width']
            top = node['y']
            bottom = node['y'] + node['height']
            
            # Handle oval shapes
            is_oval = node.get('shape') == 'oval'
            
            if is_oval:
                # For ovals, calculate intersection with ellipse
                cx = (left + right) / 2
                cy = (top + bottom) / 2
                rx = node['width'] / 2
                ry = node['height'] / 2
                
                # Direction from x1,y1 to x2,y2
                dx = x2 - x1
                dy = y2 - y1
                length = (dx*dx + dy*dy)**0.5
                if length < 1e-6:
                    return x2, y2
                
                # Normalize direction
                dx_norm = dx / length
                dy_norm = dy / length
                
                # Calculate intersection with ellipse
                # Parametric: point = (cx + rx*cos(t), cy + ry*sin(t))
                # We need to find t where line from (x1,y1) in direction (dx,dy) intersects ellipse
                # Approximation: Move from center towards direction until we hit boundary
                t = min(rx, ry) * 0.9  # Start near edge
                intersect_x = cx + dx_norm * t * (rx / min(rx, ry))
                intersect_y = cy + dy_norm * t * (ry / min(rx, ry))
                
                return intersect_x, intersect_y
            else:
                # Rectangle intersection
                # Direction vector
                dx = x2 - x1
                dy = y2 - y1
                
                # Avoid division by zero
                if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                    return x2, y2
                
                # Find intersection with each side
                candidates = []
                if abs(dx) > 1e-6:
                    # Left side
                    t = (left - x1) / dx
                    y = y1 + t * dy
                    if 0 < t <= 1 and top <= y <= bottom:
                        candidates.append((left, y, t))
                    # Right side
                    t = (right - x1) / dx
                    y = y1 + t * dy
                    if 0 < t <= 1 and top <= y <= bottom:
                        candidates.append((right, y, t))
                
                if abs(dy) > 1e-6:
                    # Top side
                    t = (top - y1) / dy
                    x = x1 + t * dx
                    if 0 < t <= 1 and left <= x <= right:
                        candidates.append((x, top, t))
                    # Bottom side
                    t = (bottom - y1) / dy
                    x = x1 + t * dx
                    if 0 < t <= 1 and left <= x <= right:
                        candidates.append((x, bottom, t))
                
                # Pick the closest intersection point
                if candidates:
                    # Sort by t parameter (closest to start point)
                    candidates.sort(key=lambda c: c[2])
                    # Return the last one (closest to target)
                    return candidates[-1][0], candidates[-1][1]
                
                return x2, y2

        # Handle all cases with segments
        if len(segments) >= 2:
            # Build path with adjusted endpoint for arrow
            path_points = []
            
            # Add all intermediate points
            for i, seg in enumerate(segments):
                if i < len(segments) - 1:
                    # All points except the last
                    path_points.extend(seg)
                else:
                    # For last segment, calculate intersection with target component
                    if len(segments) >= 2:
                        # Get second-to-last point
                        prev_x, prev_y = segments[-2]
                        target_x, target_y = seg
                        
                        # Calculate where arrow should stop at component edge
                        intersect_x, intersect_y = get_edge_intersection(
                            prev_x, prev_y, target_x, target_y, to_node
                        )
                        
                        path_points.extend([intersect_x, intersect_y])
                    else:
                        path_points.extend(seg)
            
            # Draw the polyline with arrow - arrow will now stop at component edge
            self.canvas.create_line(*path_points, fill=color, width=1.2, 
                                   arrow='last', arrowshape=(9.6, 12, 4.8), smooth=False)
            
            # Draw label (prefer persisted absolute position if available)
            if label:
                label_pos = edge.get('label_pos')
                if isinstance(label_pos, dict) and 'x' in label_pos and 'y' in label_pos:
                    mid_x = float(label_pos['x'])
                    mid_y = float(label_pos['y'])
                else:
                    label_offset = edge.get('label_offset', 0.5)
                    total_segments = len(path_points) // 2 - 1
                    if total_segments > 0:
                        target_segment = int(label_offset * total_segments)
                        target_segment = max(0, min(target_segment, total_segments - 1))
                        seg_idx = target_segment * 2
                        mid_x = (path_points[seg_idx] + path_points[seg_idx + 2]) / 2
                        mid_y = (path_points[seg_idx + 1] + path_points[seg_idx + 3]) / 2
                    else:
                        # Fallback for single segment
                        mid_x = (path_points[0] + path_points[2]) / 2
                        mid_y = (path_points[1] + path_points[3]) / 2
                
                box_id = self.canvas.create_rectangle(mid_x - 30, mid_y - 8, mid_x + 30, mid_y + 8,
                                            fill='white', outline=color, width=1, tags='flow_label')
                text_id = self.canvas.create_text(mid_x, mid_y, text=label, font=('Segoe UI', 7),
                                       fill='#2c3e50', anchor='center', tags='flow_label')
                
                # Store edge index for this label so it can be dragged (both directions)
                self.label_items[box_id] = edge_idx
                self.label_items[text_id] = edge_idx
                self.edge_to_label_items[edge_idx] = [box_id, text_id]
                logger.debug(f"Tracked label for edge {edge_idx}: box={box_id}, text={text_id}")
            return
        
        # Fallback for edges with no segments - use node centers with intersection
        logger.warning(f"Edge {from_id} -> {to_id} has no segments, using node centers")
        
        # Calculate intersection for arrow placement
        intersect_x, intersect_y = get_edge_intersection(from_x, from_y, to_x, to_y, to_node)
        
        self.canvas.create_line(from_x, from_y, intersect_x, intersect_y,
                               fill=color, width=1.2, arrow='last', arrowshape=(9.6, 12, 4.8))
        if label:
            label_offset = edge.get('label_offset', 0.5)
            mid_x = from_x + (intersect_x - from_x) * label_offset
            mid_y = from_y + (intersect_y - from_y) * label_offset
            
            box_id = self.canvas.create_rectangle(mid_x - 30, mid_y - 8, mid_x + 30, mid_y + 8,
                                        fill='white', outline=color, width=1, tags='flow_label')
            text_id = self.canvas.create_text(mid_x, mid_y, text=label, font=('Segoe UI', 7),
                                   fill='#2c3e50', anchor='center', tags='flow_label')
            
            # Store edge index for this label so it can be dragged (both directions)
            self.label_items[box_id] = edge_idx
            self.label_items[text_id] = edge_idx
            self.edge_to_label_items[edge_idx] = [box_id, text_id]
            logger.debug(f"Tracked fallback label for edge {edge_idx}: box={box_id}, text={text_id}")

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
        # Track which edge we're redrawing so we update it instead of creating a new one
        self.redraw_edge_index = choice
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
        """Delete an existing flow line with scrollable list dialog grouped by area"""
        edges = self.area_data.get('edges', [])
        if not edges:
            messagebox.showwarning("No Flows", "No flow lines to delete")
            return
        
        # Create custom dialog with scrollable listbox
        dialog = tk.Toplevel(self.canvas)
        dialog.title("Delete Flow Line")
        dialog.transient(self.canvas)
        dialog.grab_set()
        
        # Larger dialog for better readability
        dialog_width = 750
        dialog_height = 550
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Title label
        title_label = tk.Label(dialog, text="Select a flow line to delete (grouped by area):", 
                              font=('Segoe UI', 12, 'bold'), pady=10)
        title_label.pack()
        
        # Info label
        info_label = tk.Label(dialog, text="⚠️  Warning: Deletion is permanent after saving", 
                             font=('Segoe UI', 9), fg='#e74c3c', pady=5)
        info_label.pack()
        
        # Frame for listbox and scrollbar
        list_frame = tk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Listbox with better font (allow multi-select)
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                    font=('Segoe UI', 9), height=20, selectmode='extended')
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Group edges by area
        edges_by_area = {}
        for i, edge in enumerate(edges):
            from_area = self._get_node_area(edge['from'])
            to_area = self._get_node_area(edge['to'])
            
            # Determine primary area
            if from_area == to_area:
                area = from_area
            else:
                area = f"{from_area} ↔ {to_area}"
            
            if area not in edges_by_area:
                edges_by_area[area] = []
            edges_by_area[area].append(i)
        
        # Populate listbox grouped by area
        edge_index_map = []  # Maps listbox index to edge index
        for area in sorted(edges_by_area.keys()):
            # Area header
            listbox.insert(tk.END, f"")
            listbox.itemconfig(tk.END, bg='#ecf0f1')
            edge_index_map.append(None)
            
            listbox.insert(tk.END, f"━━━ {area} ━━━")
            listbox.itemconfig(tk.END, bg='#e74c3c', fg='white')
            edge_index_map.append(None)
            
            # Edges in this area
            for edge_idx in edges_by_area[area]:
                edge = edges[edge_idx]
                segments = edge.get('segments', [])
                flow_type = edge.get('flow_type', 'unknown')
                volume = edge.get('volume', 0)
                
                # Format node names
                from_name = self._format_node_name(edge['from'])
                to_name = self._format_node_name(edge['to'])
                
                # Color indicator for flow type
                type_emoji = {
                    'clean': '🔵',
                    'dirty': '🔴',
                    'wastewater': '🔴',
                    'ug_return': '🟠',
                    'dewatering': '🔴',
                    'recirculation': '🟣',
                    'evaporation': '⚫'
                }.get(flow_type.lower(), '⚪')
                
                # Status indicator
                status = f"{len(segments)}pts"
                
                display_text = f"  {from_name} → {to_name} | {type_emoji} {flow_type} | {volume:,.0f} m³ | {status}"
                listbox.insert(tk.END, display_text)
                edge_index_map.append(edge_idx)
        
        # Result variable (multiple indices)
        selected_indices = []
        
        def on_delete():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a flow line to delete")
                return
            # Map selected list rows to valid edge indices, ignoring headers
            chosen_edges = []
            for list_idx in selection:
                if list_idx < len(edge_index_map) and edge_index_map[list_idx] is not None:
                    chosen_edges.append(edge_index_map[list_idx])
            if not chosen_edges:
                messagebox.showwarning("Invalid Selection", "Please select flow lines (not headers)")
                return
            selected_indices[:] = sorted(set(chosen_edges))
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Button frame
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        delete_btn = tk.Button(btn_frame, text="🗑️ Delete Selected", command=on_delete,
                               bg='#e74c3c', fg='white', font=('Segoe UI', 10, 'bold'),
                               padx=20, pady=5)
        delete_btn.pack(side='left', padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel,
                               bg='#95a5a6', fg='white', font=('Segoe UI', 10),
                               padx=20, pady=5)
        cancel_btn.pack(side='left', padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # Process deletion if a selection was made
        if selected_indices:
            # Build confirmation summary
            lines = []
            for idx in selected_indices:
                e = edges[idx]
                lines.append(f"- {self._format_node_name(e['from'])} → {self._format_node_name(e['to'])} ({e.get('flow_type', 'unknown')}, {e.get('volume', 0):,.0f} m³)")
            if messagebox.askyesno("Confirm Delete", 
                                  "Delete selected flow lines?\n\n" + "\n".join(lines)):
                # Delete in reverse order to keep indices valid
                for idx in sorted(selected_indices, reverse=True):
                    edge = edges.pop(idx)
                    logger.info(f"🗑️ Deleted flow: {edge['from']} → {edge['to']}")
                self._draw_diagram()
                messagebox.showinfo("Deleted", f"Removed {len(selected_indices)} flow line(s)")

    def _straighten_line(self):
        """Straighten an existing flow line with scrollable list dialog grouped by area"""
        edges = self.area_data.get('edges', [])
        if not edges:
            messagebox.showwarning("No Flows", "No flow lines to straighten")
            return
        
        # Create custom dialog with scrollable listbox
        dialog = tk.Toplevel(self.canvas)
        dialog.title("Straighten Flow Line")
        dialog.transient(self.canvas)
        dialog.grab_set()
        
        # Larger dialog for better readability
        dialog_width = 750
        dialog_height = 550
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Title label
        title_label = tk.Label(dialog, text="Select a flow line to straighten (grouped by area):", 
                              font=('Segoe UI', 12, 'bold'), pady=10)
        title_label.pack()
        
        # Info label
        info_label = tk.Label(dialog, text="📏 Straightening removes intermediate waypoints, creating direct line from start to end", 
                             font=('Segoe UI', 9), fg='#7f8c8d', pady=5)
        info_label.pack()
        
        # Frame for listbox and scrollbar
        list_frame = tk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Listbox with better font
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                            font=('Segoe UI', 9), height=20, selectmode='single')
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Group edges by area
        edges_by_area = {}
        for i, edge in enumerate(edges):
            from_area = self._get_node_area(edge['from'])
            to_area = self._get_node_area(edge['to'])
            
            # Determine primary area
            if from_area == to_area:
                area = from_area
            else:
                area = f"{from_area} ↔ {to_area}"
            
            if area not in edges_by_area:
                edges_by_area[area] = []
            edges_by_area[area].append(i)
        
        # Populate listbox grouped by area
        edge_index_map = []  # Maps listbox index to edge index
        for area in sorted(edges_by_area.keys()):
            # Area header
            listbox.insert(tk.END, f"")
            listbox.itemconfig(tk.END, bg='#ecf0f1')
            edge_index_map.append(None)
            
            listbox.insert(tk.END, f"━━━ {area} ━━━")
            listbox.itemconfig(tk.END, bg='#3498db', fg='white')
            edge_index_map.append(None)
            
            # Edges in this area
            for edge_idx in edges_by_area[area]:
                edge = edges[edge_idx]
                segments = edge.get('segments', [])
                flow_type = edge.get('flow_type', 'unknown')
                volume = edge.get('volume', 0)
                
                # Format node names
                from_name = self._format_node_name(edge['from'])
                to_name = self._format_node_name(edge['to'])
                
                # Color indicator for flow type
                type_emoji = {
                    'clean': '🔵',
                    'dirty': '🔴',
                    'wastewater': '🔴',
                    'ug_return': '🟠',
                    'dewatering': '🔴',
                    'recirculation': '🟣',
                    'evaporation': '⚫'
                }.get(flow_type.lower(), '⚪')
                
                # Status indicator
                status = f"{len(segments)}pts" if len(segments) > 2 else "straight"
                status_emoji = "📐" if len(segments) <= 2 else "〰️"
                
                display_text = f"  {status_emoji} {from_name} → {to_name} | {type_emoji} {flow_type} | {volume:,.0f} m³ | {status}"
                listbox.insert(tk.END, display_text)
                
                # Color coding
                if len(segments) <= 2:
                    listbox.itemconfig(tk.END, fg='#95a5a6')  # Gray for already straight
                
                edge_index_map.append(edge_idx)
        
        # Result variable
        selected_index = [None]
        
        def on_straighten():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a flow line to straighten")
                return
            
            list_idx = selection[0]
            if list_idx >= len(edge_index_map) or edge_index_map[list_idx] is None:
                messagebox.showwarning("Invalid Selection", "Please select a flow line (not a header)")
                return
            
            selected_index[0] = edge_index_map[list_idx]
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Button frame
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        straighten_btn = tk.Button(btn_frame, text="📏 Straighten Selected", command=on_straighten,
                               bg='#16a085', fg='white', font=('Segoe UI', 10, 'bold'),
                               padx=20, pady=5)
        straighten_btn.pack(side='left', padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel,
                               bg='#95a5a6', fg='white', font=('Segoe UI', 10),
                               padx=20, pady=5)
        cancel_btn.pack(side='left', padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # Process straightening if a selection was made
        if selected_index[0] is not None:
            self._straighten_edge(selected_index[0])

    def _start_drawing(self):
        """Start manual flow line drawing"""
        self.drawing_mode = True
        self.drawing_segments = []
        self.drawing_from = None
        self.drawing_to = None
        self.canvas.config(cursor='crosshair')
        messagebox.showinfo("Draw Mode", 
                           "🔧 SNAP TO COMPONENT MODE\n\n"
                           "1. Click FROM component (snaps to nearest edge)\n"
                           "2. Move mouse - see orange anchors appear\n"
                           "3. Click TO component (snaps to nearest edge)\n"
                           "4. Add intermediate points by clicking canvas\n"
                           "5. Right-click to cancel\n\n"
                           "⭕ Orange anchors = snap points (within 30px)")


    def _on_canvas_click(self, event):
        """Handle click"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Drawing mode
        if self.drawing_mode:
            # Check if clicked on node
            clicked_node = self._get_node_at(canvas_x, canvas_y)
            if self.drawing_from is None:
                # First click - select FROM component and choose anchor point
                if clicked_node:
                    self.drawing_from = clicked_node
                    # Find nearest anchor point to snap start
                    snap_point = self._find_nearest_anchor(clicked_node, canvas_x, canvas_y)
                    if snap_point:
                        self.drawing_segments = [snap_point]
                        messagebox.showinfo("From Selected", 
                                          f"Drawing from: {clicked_node}\n"
                                          f"Start point snapped to component edge\n"
                                          f"Click to add path points or click target component")
                    else:
                        self.drawing_segments = [(canvas_x, canvas_y)]
                        messagebox.showinfo("From Selected", f"Drawing from: {clicked_node}\nClick to add path points or click target component")
                else:
                    messagebox.showwarning("Invalid", "Click on a component to start")
            elif clicked_node and clicked_node != self.drawing_from:
                # Clicked on a component - finish drawing at snapped endpoint
                snap_point = self._find_nearest_anchor(clicked_node, canvas_x, canvas_y)
                if snap_point:
                    self.drawing_segments.append(snap_point)
                else:
                    self.drawing_segments.append((canvas_x, canvas_y))
                # Create edge with user-defined path
                self._finish_drawing(self.drawing_from, clicked_node)
            else:
                # Clicked on canvas - add segment point at exact location
                if len(self.drawing_segments) > 0:
                    # Add intermediate point at exact click location
                    self.drawing_segments.append((canvas_x, canvas_y))
                    self._draw_diagram()
            return

        # Check if clicked on a flow label
        clicked_items = self.canvas.find_overlapping(canvas_x - 2, canvas_y - 2, canvas_x + 2, canvas_y + 2)
        logger.debug(f"Clicked items: {clicked_items}, label_items keys: {list(self.label_items.keys())}")
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
        
        # Label dragging - move canvas items directly for smooth dragging
        if self.dragging_label and self.dragged_label_edge_idx is not None:
            edges = self.area_data.get('edges', [])
            if self.dragged_label_edge_idx < len(edges):
                edge = edges[self.dragged_label_edge_idx]
                
                # Calculate new label position
                from_id = edge.get('from')
                to_id = edge.get('to')
                
                if from_id in self.nodes_by_id and to_id in self.nodes_by_id:
                    # Build path points from segments
                    segments = edge.get('segments', [])
                    
                    if len(segments) >= 2:
                        path_points = segments[:]
                    else:
                        from_node = self.nodes_by_id[from_id]
                        to_node = self.nodes_by_id[to_id]
                        from_x = from_node['x'] + from_node['width'] / 2
                        from_y = from_node['y'] + from_node['height'] / 2
                        to_x = to_node['x'] + to_node['width'] / 2
                        to_y = to_node['y'] + to_node['height'] / 2
                        path_points = [(from_x, from_y), (to_x, to_y)]
                    
                    # Find closest point on path to mouse
                    min_dist = float('inf')
                    best_offset = 0.5
                    closest_x, closest_y = canvas_x, canvas_y
                    
                    for i in range(len(path_points) - 1):
                        x1, y1 = path_points[i]
                        x2, y2 = path_points[i + 1]
                        
                        segment_len = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                        if segment_len > 0:
                            t = max(0, min(1, ((canvas_x - x1) * (x2 - x1) + (canvas_y - y1) * (y2 - y1)) / segment_len**2))
                            cx = x1 + t * (x2 - x1)
                            cy = y1 + t * (y2 - y1)
                            dist = ((canvas_x - cx)**2 + (canvas_y - cy)**2)**0.5
                            
                            if dist < min_dist:
                                min_dist = dist
                                best_offset = (i + t) / (len(path_points) - 1)
                                closest_x, closest_y = cx, cy
                    
                    # Persist exact label coordinates for stable redraws
                    edge['label_offset'] = best_offset
                    edge['label_pos'] = {'x': closest_x, 'y': closest_y}
                    
                    # Move the label canvas items directly (smooth visual feedback)
                    if self.dragged_label_edge_idx in self.edge_to_label_items:
                        box_id, text_id = self.edge_to_label_items[self.dragged_label_edge_idx]
                        # Update box position
                        self.canvas.coords(box_id, closest_x - 30, closest_y - 8, closest_x + 30, closest_y + 8)
                        # Update text position
                        self.canvas.coords(text_id, closest_x, closest_y)
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
        old_x, old_y = node['x'], node['y']
        node['x'] += dx
        node['y'] += dy

        if self.snap_to_grid:
            node['x'] = round(node['x'] / self.grid_size) * self.grid_size
            node['y'] = round(node['y'] / self.grid_size) * self.grid_size

        # Update connected edges to follow the component
        actual_dx = node['x'] - old_x
        actual_dy = node['y'] - old_y
        self._update_connected_edges(self.selected_node, actual_dx, actual_dy)

        self.drag_start_x = canvas_x
        self.drag_start_y = canvas_y
        self._draw_diagram()

    def _on_canvas_release(self, event):
        """Handle release"""
        # If we were dragging a label, redraw once to finalize position
        was_dragging_label = self.dragging_label
        
        self.dragging = False
        self.dragging_label = False
        self.dragged_label_edge_idx = None
        
        # Redraw only once after label drag is complete
        if was_dragging_label:
            self._draw_diagram()
            logger.info("✅ Label position saved")

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
        """Handle mouse motion - show preview line and anchor snap feedback when drawing"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Check for hovered anchor points during drawing mode
        if self.drawing_mode:
            old_hover = self.hovered_anchor
            self.hovered_anchor = None
            
            # Find if hovering near any anchor point
            for node_id, anchors in self.snap_anchor_points.items():
                for anchor_name, (ax, ay) in anchors.items():
                    if anchor_name == 'center':
                        continue
                    dist = ((canvas_x - ax)**2 + (canvas_y - ay)**2)**0.5
                    if dist <= self.snap_distance:
                        self.hovered_anchor = {'node_id': node_id, 'name': anchor_name}
                        if old_hover != self.hovered_anchor:
                            self._draw_diagram()  # Redraw to show highlighted anchor
                        return
            
            # If we were hovering and now aren't, redraw
            if old_hover:
                self._draw_diagram()
        
        if not self.drawing_mode or len(self.drawing_segments) == 0:
            return

        # Only redraw if we have a preview line tag
        if hasattr(self, '_preview_line_id') and self._preview_line_id:
            self.canvas.delete(self._preview_line_id)
        
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

    def _show_flow_type_dialog(self, from_id, to_id):
        """Show professional flow type selection dialog with scrollable options"""
        dialog = tk.Toplevel(self.canvas)
        dialog.title("Select Flow Type")
        dialog.transient(self.canvas)
        dialog.grab_set()
        
        # Center the dialog with reasonable height; scrolling keeps options visible on small screens
        dialog_width = 450
        dialog_height = 560
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.minsize(dialog_width, dialog_height)
        
        # Header (fixed at top)
        header = tk.Label(dialog, text=f"Creating Flow Line", 
                         font=('Segoe UI', 12, 'bold'), bg='#3498db', fg='white', pady=10)
        header.pack(fill='x')
        
        # Connection info (fixed)
        info_frame = tk.Frame(dialog, bg='#ecf0f1', pady=10)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(info_frame, text=f"From:", font=('Segoe UI', 9, 'bold'), 
                bg='#ecf0f1').pack(anchor='w', padx=10)
        tk.Label(info_frame, text=from_id, font=('Segoe UI', 10), 
                bg='#ecf0f1', fg='#2c3e50').pack(anchor='w', padx=20)
        
        tk.Label(info_frame, text=f"To:", font=('Segoe UI', 9, 'bold'), 
                bg='#ecf0f1').pack(anchor='w', padx=10, pady=(5,0))
        tk.Label(info_frame, text=to_id, font=('Segoe UI', 10), 
                bg='#ecf0f1', fg='#2c3e50').pack(anchor='w', padx=20)
        
        # Flow type selection label
        tk.Label(dialog, text="Select Flow Type:", 
                font=('Segoe UI', 10, 'bold'), pady=5).pack(anchor='w', padx=10)
        
        # Scrollable container for flow types
        scroll_container = tk.Frame(dialog)
        scroll_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Canvas for scrolling
        canvas = tk.Canvas(scroll_container, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        
        # Frame inside canvas for content
        radio_frame = tk.Frame(canvas)
        
        # Configure canvas scrolling
        radio_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=radio_frame, anchor="nw", width=410)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        flow_types = [
            ("clean", "Clean Water", "Potable/treated water", "#4b78a8"),
            ("dirty", "Dirty Water", "Wastewater", "#e74c3c"),
            ("dewatering", "Dewatering", "Mine water/drainage", "#e74c3c"),
            ("ug_return", "Underground Return", "UG return water", "#e74c3c"),
            ("process_dirty", "Process Dirty", "Plant dirty water", "#e74c3c"),
            ("stormwater", "Stormwater", "Rainfall runoff", "#e74c3c"),
            ("recirculation", "Recirculation", "Internal return loop", "#9b59b6"),
            ("evaporation", "Evaporation", "Loss to air", "#000000")
        ]
        
        selected_type = tk.StringVar(value="clean")
        
        for value, label, desc, color in flow_types:
            frame = tk.Frame(radio_frame, relief='solid', borderwidth=1, bg='white')
            frame.pack(fill='x', pady=2)
            
            rb = tk.Radiobutton(frame, text=label, variable=selected_type, value=value,
                               font=('Segoe UI', 10, 'bold'), bg='white', 
                               activebackground='#ecf0f1')
            rb.pack(anchor='w', padx=5, pady=2)
            
            desc_label = tk.Label(frame, text=desc, font=('Segoe UI', 8), 
                                 fg='#7f8c8d', bg='white')
            desc_label.pack(anchor='w', padx=25)
            
            color_label = tk.Label(frame, text="●", font=('Segoe UI', 16), 
                                  fg=color, bg='white')
            color_label.place(relx=0.95, rely=0.5, anchor='e')
        
        result = [None]
        
        def on_ok():
            result[0] = selected_type.get()
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        
        def on_cancel():
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        
        # Buttons (fixed at bottom)
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10, fill='x')

        ok_btn = tk.Button(btn_frame, text="OK", command=on_ok,
                  bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
                  padx=30, pady=6, width=12)
        ok_btn.pack(side='left', padx=10, expand=True)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel,
                      bg='#95a5a6', fg='white', font=('Segoe UI', 10),
                      padx=30, pady=6, width=12)
        cancel_btn.pack(side='left', padx=10, expand=True)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        
        dialog.wait_window()
        return result[0]

    def _show_volume_dialog(self, from_id, to_id, flow_type):
        """Show professional volume input dialog"""
        dialog = tk.Toplevel(self.canvas)
        dialog.title("Enter Flow Volume")
        dialog.transient(self.canvas)
        dialog.grab_set()
        
        # Center the dialog
        dialog_width = 520
        dialog_height = 320
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.minsize(dialog_width, dialog_height)
        
        # Header
        header = tk.Label(dialog, text=f"Flow Volume", 
                         font=('Segoe UI', 12, 'bold'), bg='#3498db', fg='white', pady=10)
        header.pack(fill='x')
        
        # Connection info
        info_frame = tk.Frame(dialog, bg='#ecf0f1', pady=15)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(info_frame, text=f"From: {from_id}", font=('Segoe UI', 9), 
                bg='#ecf0f1').pack(anchor='w', padx=10)
        tk.Label(info_frame, text=f"To: {to_id}", font=('Segoe UI', 9), 
                bg='#ecf0f1').pack(anchor='w', padx=10)
        tk.Label(info_frame, text=f"Type: {flow_type.title()}", font=('Segoe UI', 9, 'bold'), 
                bg='#ecf0f1', fg='#2980b9').pack(anchor='w', padx=10, pady=(5,0))
        
        # Volume input
        input_frame = tk.Frame(dialog)
        input_frame.pack(pady=15, padx=10, fill='x')
        
        tk.Label(input_frame, text="Volume (m³/month):", 
            font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        
        volume_var = tk.StringVar()
        volume_entry = tk.Entry(input_frame, textvariable=volume_var, 
                               font=('Segoe UI', 12), width=15)
        volume_entry.pack(side='left', padx=5)
        volume_entry.focus_set()
        
        error_label = tk.Label(dialog, text="", font=('Segoe UI', 9), fg='#e74c3c')
        error_label.pack()
        
        result = [None]
        
        def validate_and_submit():
            try:
                val = float(volume_var.get())
                if val < 0:
                    error_label.config(text="Volume must be positive")
                    return
                result[0] = val
                dialog.destroy()
            except ValueError:
                error_label.config(text="Please enter a valid number")
        
        def on_cancel():
            dialog.destroy()
        
        # Bind Enter key
        volume_entry.bind('<Return>', lambda e: validate_and_submit())
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15, fill='x')

        ok_btn = tk.Button(btn_frame, text="OK", command=validate_and_submit,
                  bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
                  padx=30, pady=6, width=12)
        ok_btn.pack(side='left', padx=10, expand=True)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel,
                      bg='#95a5a6', fg='white', font=('Segoe UI', 10),
                      padx=30, pady=6, width=12)
        cancel_btn.pack(side='left', padx=10, expand=True)
        
        dialog.wait_window()
        return result[0]

    def _finish_drawing(self, from_id, to_id):
        """Finish drawing and create or update edge with smart edge connections"""
        edges = self.area_data.get('edges', [])
        
        # Get flow type using custom dialog
        flow_type = self._show_flow_type_dialog(from_id, to_id)
        if not flow_type:
            messagebox.showwarning("Cancelled", "Flow type required. Drawing cancelled.")
            self.drawing_mode = False
            self.drawing_segments = []
            self.drawing_from = None
            self.canvas.config(cursor='hand2')
            self._draw_diagram()
            return

        # Get volume using custom dialog
        volume = self._show_volume_dialog(from_id, to_id, flow_type)
        if volume is None:
            messagebox.showwarning("Cancelled", "Volume required. Drawing cancelled.")
            self.drawing_mode = False
            self.drawing_segments = []
            self.drawing_from = None
            self.canvas.config(cursor='hand2')
            self._draw_diagram()
            return

        # If we're redrawing, update the selected edge
        existing_idx = self.redraw_edge_index

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
                'label': label
            }
            edges.append(new_edge)
            logger.info(f"✅ Created flow: {from_id} → {to_id} ({flow_type}, {label} m³)")

        self.area_data['edges'] = edges
        self.drawing_mode = False
        self.drawing_segments = []
        self.drawing_from = None
        # Reset redraw state
        self.redraw_edge_index = None
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
