"""
Simple Interactive Flow Diagram Editor
Allows you to manually add and edit components without coding
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path

class FlowDiagramEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Flow Diagram Editor - UG2 North Decline")
        self.root.geometry("1000x700")
        
        self.config = {}
        self.nodes = []
        self.edges = []
        
        self._setup_ui()
        self._load_diagram()
    
    def _setup_ui(self):
        """Create the editor UI"""
        # Top frame - buttons
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(top_frame, text="Load Diagram", command=self._load_diagram).pack(side='left', padx=2)
        ttk.Button(top_frame, text="Save Diagram", command=self._save_diagram).pack(side='left', padx=2)
        ttk.Button(top_frame, text="Add Node", command=self._add_node_dialog).pack(side='left', padx=2)
        ttk.Button(top_frame, text="Add Edge", command=self._add_edge_dialog).pack(side='left', padx=2)
        ttk.Button(top_frame, text="Delete Selected", command=self._delete_selected).pack(side='left', padx=2)
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Nodes tab
        nodes_frame = ttk.Frame(notebook)
        notebook.add(nodes_frame, text="Nodes (Components)")
        
        self.nodes_tree = ttk.Treeview(nodes_frame, columns=('ID', 'Label', 'X', 'Y', 'Width', 'Height', 'Type'), height=20)
        self.nodes_tree.heading('#0', text='#')
        self.nodes_tree.column('#0', width=40)
        self.nodes_tree.heading('ID', text='Component ID')
        self.nodes_tree.column('ID', width=120)
        self.nodes_tree.heading('Label', text='Label')
        self.nodes_tree.column('Label', width=150)
        self.nodes_tree.heading('X', text='X')
        self.nodes_tree.column('X', width=50)
        self.nodes_tree.heading('Y', text='Y')
        self.nodes_tree.column('Y', width=50)
        self.nodes_tree.heading('Width', text='Width')
        self.nodes_tree.column('Width', width=50)
        self.nodes_tree.heading('Height', text='Height')
        self.nodes_tree.column('Height', width=50)
        self.nodes_tree.heading('Type', text='Type')
        self.nodes_tree.column('Type', width=100)
        
        self.nodes_tree.pack(fill='both', expand=True)
        
        # Edges tab
        edges_frame = ttk.Frame(notebook)
        notebook.add(edges_frame, text="Edges (Connections)")
        
        self.edges_tree = ttk.Treeview(edges_frame, columns=('From', 'To', 'Value', 'Label', 'Color'), height=20)
        self.edges_tree.heading('#0', text='#')
        self.edges_tree.column('#0', width=40)
        self.edges_tree.heading('From', text='From')
        self.edges_tree.column('From', width=120)
        self.edges_tree.heading('To', text='To')
        self.edges_tree.column('To', width=120)
        self.edges_tree.heading('Value', text='Value (m³)')
        self.edges_tree.column('Value', width=80)
        self.edges_tree.heading('Label', text='Label')
        self.edges_tree.column('Label', width=150)
        self.edges_tree.heading('Color', text='Color')
        self.edges_tree.column('Color', width=80)
        
        self.edges_tree.pack(fill='both', expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief='sunken').pack(fill='x', side='bottom')
    
    def _load_diagram(self):
        """Load diagram from JSON"""
        json_path = Path('data/diagrams/ug2_north_decline.json')
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    self.config = json.load(f)
                self.nodes = self.config.get('nodes', [])
                self.edges = self.config.get('edges', [])
                self._refresh_trees()
                self.status_var.set(f"Loaded: {len(self.nodes)} nodes, {len(self.edges)} edges")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
    
    def _save_diagram(self):
        """Save diagram back to JSON"""
        try:
            self.config['nodes'] = self.nodes
            self.config['edges'] = self.edges
            
            json_path = Path('data/diagrams/ug2_north_decline.json')
            with open(json_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.status_var.set("✅ Saved successfully!")
            messagebox.showinfo("Success", "Diagram saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def _refresh_trees(self):
        """Refresh the tree views"""
        # Clear and reload nodes
        for item in self.nodes_tree.get_children():
            self.nodes_tree.delete(item)
        
        for i, node in enumerate(self.nodes):
            self.nodes_tree.insert('', 'end', text=str(i), values=(
                node.get('id', ''),
                node.get('label', ''),
                node.get('x', ''),
                node.get('y', ''),
                node.get('width', ''),
                node.get('height', ''),
                node.get('type', '')
            ))
        
        # Clear and reload edges
        for item in self.edges_tree.get_children():
            self.edges_tree.delete(item)
        
        for i, edge in enumerate(self.edges):
            self.edges_tree.insert('', 'end', text=str(i), values=(
                edge.get('from', ''),
                edge.get('to', ''),
                edge.get('value', ''),
                edge.get('label', ''),
                edge.get('color', '')
            ))
    
    def _add_node_dialog(self):
        """Add a new node"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Component (Node)")
        dialog.geometry("400x500")
        
        # Fields
        fields = {
            'id': 'Component ID (e.g., guest_house)',
            'label': 'Label (use \\n for new line)',
            'type': 'Type (source/storage/treatment/consumption/process/loss)',
            'x': 'X Position',
            'y': 'Y Position',
            'width': 'Width',
            'height': 'Height',
            'fill': 'Fill Color (e.g., #5d88b6)',
            'outline': 'Outline Color'
        }
        
        entries = {}
        
        for i, (key, label) in enumerate(fields.items()):
            ttk.Label(dialog, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[key] = entry
        
        def save_node():
            node = {key: entry.get() for key, entry in entries.items()}
            # Convert numeric values
            node['x'] = float(node['x']) if node['x'] else 0
            node['y'] = float(node['y']) if node['y'] else 0
            node['width'] = float(node['width']) if node['width'] else 140
            node['height'] = float(node['height']) if node['height'] else 50
            node['shape'] = 'rect'
            
            self.nodes.append(node)
            self._refresh_trees()
            dialog.destroy()
            self.status_var.set(f"Added node: {node['id']}")
        
        ttk.Button(dialog, text="Save Node", command=save_node).grid(row=len(fields), column=1, pady=10)
    
    def _add_edge_dialog(self):
        """Add a new edge (connection)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Connection (Edge)")
        dialog.geometry("400x300")
        
        fields = {
            'from': 'From Component ID',
            'to': 'To Component ID',
            'value': 'Flow Value (m³)',
            'label': 'Label (e.g., "1 470")',
            'color': 'Line Color (e.g., #4b78a8)'
        }
        
        entries = {}
        
        for i, (key, label) in enumerate(fields.items()):
            ttk.Label(dialog, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[key] = entry
        
        def save_edge():
            edge = {key: entry.get() for key, entry in entries.items()}
            edge['value'] = float(edge['value']) if edge['value'] else 0
            
            self.edges.append(edge)
            self._refresh_trees()
            dialog.destroy()
            self.status_var.set(f"Added edge: {edge['from']} → {edge['to']}")
        
        ttk.Button(dialog, text="Save Connection", command=save_edge).grid(row=len(fields), column=1, pady=10)
    
    def _delete_selected(self):
        """Delete selected item"""
        # Check which tree is focused
        focus = self.root.focus_get()
        
        if focus == self.nodes_tree or isinstance(focus, tk.Widget) and 'nodes' in str(focus):
            selection = self.nodes_tree.selection()
            if selection:
                indices = [int(self.nodes_tree.item(item, '#0')) for item in selection]
                for i in sorted(indices, reverse=True):
                    if i < len(self.nodes):
                        self.nodes.pop(i)
                self._refresh_trees()
                self.status_var.set("Node deleted")
        
        elif focus == self.edges_tree or isinstance(focus, tk.Widget) and 'edges' in str(focus):
            selection = self.edges_tree.selection()
            if selection:
                indices = [int(self.edges_tree.item(item, '#0')) for item in selection]
                for i in sorted(indices, reverse=True):
                    if i < len(self.edges):
                        self.edges.pop(i)
                self._refresh_trees()
                self.status_var.set("Edge deleted")

if __name__ == '__main__':
    root = tk.Tk()
    app = FlowDiagramEditor(root)
    root.mainloop()
