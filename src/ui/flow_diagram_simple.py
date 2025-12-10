"""
Simple, Clean Flow Diagram - Easy to understand and modify
Connects components with visual flows showing water movement
"""

import json
import tkinter as tk
from tkinter import Canvas, Frame, Label, Scrollbar, ttk
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.app_logger import logger


class SimpleFlowDiagram:
    """Simple flow diagram that's easy to read and modify"""

    def __init__(self, parent):
        self.parent = parent
        self.canvas = None
        self.area_data = {}

    def load(self):
        """Load and display the diagram"""
        for widget in self.parent.winfo_children():
            widget.destroy()

        self._create_ui()
        self._load_diagram_data()
        logger.info("✅ Simple flow diagram loaded")

    def _create_ui(self):
        """Create the UI structure"""
        # Header
        header = Frame(self.parent, bg='#2c3e50', height=100)
        header.pack(fill='x', padx=0, pady=0)

        title = Label(header, text='WATER FLOW DIAGRAM', 
                     font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='white')
        title.pack(pady=10)

        # Canvas with scrollbars
        canvas_frame = Frame(self.parent)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.canvas = Canvas(canvas_frame, bg='#f8f9fa', highlightthickness=0)
        vscroll = Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        hscroll = Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        vscroll.grid(row=0, column=1, sticky='ns')
        hscroll.grid(row=1, column=0, sticky='ew')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas.configure(scrollregion=(0, 0, 2400, 1200))

    def _load_diagram_data(self):
        """Load diagram configuration from JSON"""
        json_file = Path(__file__).parent.parent.parent / 'data' / 'diagrams' / 'ug2_north_decline.json'
        
        if not json_file.exists():
            self.canvas.create_text(400, 50, text="Diagram data not found", font=('Arial', 12), fill='red')
            return

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.area_data = json.load(f)
            logger.info(f"✅ Loaded diagram: {self.area_data.get('title')}")
            self._draw_diagram()
        except Exception as e:
            logger.error(f"❌ Error loading diagram: {e}")
            self.canvas.create_text(400, 50, text=f"Error: {e}", font=('Arial', 12), fill='red')

    def _draw_diagram(self):
        """Draw the complete diagram"""
        if not self.area_data:
            return

        self.canvas.delete('all')

        # Draw title
        title = self.area_data.get('title', 'Flow Diagram')
        self.canvas.create_text(50, 30, text=title, font=('Segoe UI', 14, 'bold'), 
                               fill='#2c3e50', anchor='nw')

        # Draw background sections
        self._draw_background_layers()

        # Draw nodes (components)
        nodes = self.area_data.get('nodes', [])
        node_positions = {}
        for node in nodes:
            x, y = node['x'], node['y']
            node_id = node['id']
            node_positions[node_id] = (x + node['width']/2, y + node['height']/2)
            self._draw_node(node)

        # Draw edges (connections/flows)
        edges = self.area_data.get('edges', [])
        for edge in edges:
            self._draw_edge(edge, node_positions)

        logger.info(f"Drew {len(nodes)} components and {len(edges)} connections")

    def _draw_background_layers(self):
        """Draw background layers to organize the diagram"""
        # Sources layer
        self.canvas.create_rectangle(20, 100, 300, 350, fill='#ecf0f1', outline='#bdc3c7', width=2)
        self.canvas.create_text(30, 110, text='SOURCES', font=('Segoe UI', 10, 'bold'), 
                               fill='#34495e', anchor='nw')

        # Treatment layer
        self.canvas.create_rectangle(320, 100, 600, 350, fill='#ecf0f1', outline='#bdc3c7', width=2)
        self.canvas.create_text(330, 110, text='TREATMENT', font=('Segoe UI', 10, 'bold'), 
                               fill='#34495e', anchor='nw')

        # Storage layer
        self.canvas.create_rectangle(620, 100, 1000, 400, fill='#ecf0f1', outline='#bdc3c7', width=2)
        self.canvas.create_text(630, 110, text='STORAGE', font=('Segoe UI', 10, 'bold'), 
                               fill='#34495e', anchor='nw')

        # Distribution layer
        self.canvas.create_rectangle(1020, 100, 1400, 400, fill='#ecf0f1', outline='#bdc3c7', width=2)
        self.canvas.create_text(1030, 110, text='DISTRIBUTION', font=('Segoe UI', 10, 'bold'), 
                               fill='#34495e', anchor='nw')

    def _draw_node(self, node):
        """Draw a single component node"""
        x = node['x']
        y = node['y']
        width = node['width']
        height = node['height']
        fill = node.get('fill', '#dfe6ed')
        outline = node.get('outline', '#2c3e50')
        label = node.get('label', '')
        node_type = node.get('type', 'process')

        # Draw shape
        if node.get('shape') == 'oval':
            self.canvas.create_oval(x, y, x+width, y+height, fill=fill, outline=outline, width=2)
        else:
            self.canvas.create_rectangle(x, y, x+width, y+height, fill=fill, outline=outline, width=2)

        # Draw label
        lines = label.split('\n') if label else []
        for idx, line in enumerate(lines):
            font = ('Segoe UI', 8, 'bold') if idx == 0 else ('Segoe UI', 7)
            self.canvas.create_text(x + width/2, y + 15 + (idx * 13), text=line, 
                                   font=font, fill='#000', anchor='center')

        # Add small type label only for inflow/source nodes
        normalized_type = (node_type or '').lower()
        if normalized_type in ('source', 'inflow', 'inflows'):
            type_label = node_type.upper()
            self.canvas.create_text(
                x + width/2,
                y + height - 5,
                text=type_label,
                font=('Segoe UI', 6),
                fill='#7f8c8d',
                anchor='s'
            )

    def _draw_edge(self, edge, node_positions):
        """Draw a connection between two nodes"""
        from_id = edge['from']
        to_id = edge['to']
        label = edge.get('label', '')
        color = edge.get('color', '#3498db')
        value = edge.get('value', 0)

        if from_id not in node_positions or to_id not in node_positions:
            return

        x1, y1 = node_positions[from_id]
        x2, y2 = node_positions[to_id]

        # Draw arrow line
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2.5, arrow='last',
                               arrowshape=(12, 15, 6))

        # Draw label at midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        if label:
            # Background for label
            self.canvas.create_rectangle(mid_x - 50, mid_y - 12, mid_x + 50, mid_y + 12,
                                        fill='white', outline=color, width=1)
            # Label text
            self.canvas.create_text(mid_x, mid_y, text=label, font=('Segoe UI', 7),
                                   fill=color, anchor='center')


# For compatibility
FlowDiagramDashboard = SimpleFlowDiagram
