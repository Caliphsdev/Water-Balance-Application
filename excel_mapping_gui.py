#!/usr/bin/env python
"""
EXCEL MAPPING MANAGER - GUI Tool
Simple point-and-click interface for managing Excel mappings
No programming knowledge required!
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import pandas as pd

class ExcelMappingManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Mapping Manager")
        self.root.geometry("1000x700")
        
        self.json_file = Path('data/diagrams/ug2_north_decline.json')
        self.excel_file = Path('test_templates/Water_Balance_TimeSeries_Template.xlsx')
        
        self.data = None
        self.edges = []
        self.excel_columns = {}
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Title
        title = ttk.Label(self.root, text="Excel Flow Mapping Manager", 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)
        
        # Instructions
        info = ttk.Label(self.root, text="Select flows and map them to Excel columns",
                        font=('Arial', 10))
        info.pack(pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10, fill='x', padx=10)
        
        ttk.Button(btn_frame, text="🔄 Auto-Map All", command=self.auto_map_all).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📂 Browse Files", command=self.browse_files).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💾 Save Changes", command=self.save_changes).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Reload", command=self.load_data).pack(side='left', padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Loading...")
        status = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        status.pack(fill='x', padx=10, pady=5)
        
        # Main content
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tree view for flows
        columns = ('Flow', 'Type', 'Sheet', 'Column', 'Status')
        self.tree = ttk.Treeview(content_frame, columns=columns, height=25)
        
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('Flow', anchor='w', width=300)
        self.tree.column('Type', anchor='w', width=100)
        self.tree.column('Sheet', anchor='w', width=120)
        self.tree.column('Column', anchor='w', width=250)
        self.tree.column('Status', anchor='w', width=80)
        
        self.tree.heading('#0', text='', anchor='w')
        self.tree.heading('Flow', text='Flow Connection', anchor='w')
        self.tree.heading('Type', text='Type', anchor='w')
        self.tree.heading('Sheet', text='Sheet', anchor='w')
        self.tree.heading('Column', text='Excel Column', anchor='w')
        self.tree.heading('Status', text='Status', anchor='w')
        
        # Scrollbars
        vsb = ttk.Scrollbar(content_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(content_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        # Grid
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', self.on_tree_double_click)
    
    def load_data(self):
        try:
            # Load JSON
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.edges = self.data.get('edges', [])
            
            # Load Excel sheets
            if self.excel_file.exists():
                xl = pd.ExcelFile(self.excel_file)
                for sheet in xl.sheet_names:
                    if sheet.startswith('Flows_'):
                        try:
                            df = pd.read_excel(self.excel_file, sheet_name=sheet, header=2)
                            self.excel_columns[sheet] = list(df.columns)
                        except:
                            self.excel_columns[sheet] = []
            
            self.refresh_tree()
            self.status_var.set(f"Loaded {len(self.edges)} flows")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
            self.status_var.set("Error loading data")
    
    def refresh_tree(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add flows
        for i, edge in enumerate(self.edges):
            from_id = edge.get('from', '')
            to_id = edge.get('to', '')
            flow_type = edge.get('flow_type', 'unknown')
            
            mapping = edge.get('excel_mapping', {})
            sheet = mapping.get('sheet', '')
            column = mapping.get('column', '')
            enabled = '✅' if mapping.get('enabled') else '❌'
            
            flow_name = f"{from_id} → {to_id}"
            
            self.tree.insert('', tk.END, iid=str(i), values=(
                flow_name,
                flow_type,
                sheet,
                column,
                enabled
            ))
    
    def on_tree_double_click(self, event):
        item = self.tree.selection()[0]
        idx = int(item)
        self.edit_mapping(idx)
    
    def edit_mapping(self, idx):
        edge = self.edges[idx]
        
        # Create edit window
        win = tk.Toplevel(self.root)
        win.title(f"Edit Mapping: {edge['from']} → {edge['to']}")
        win.geometry("600x400")
        
        # Flow info
        ttk.Label(win, text=f"Flow: {edge['from']} → {edge['to']}", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        ttk.Label(win, text=f"Type: {edge.get('flow_type')}").pack()
        
        # Mapping options
        ttk.Label(win, text="Excel Mapping:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Enable checkbox
        enabled_var = tk.BooleanVar(value=edge.get('excel_mapping', {}).get('enabled', False))
        ttk.Checkbutton(win, text="Enable Excel mapping", variable=enabled_var).pack(anchor='w', padx=20)
        
        # Sheet selection
        ttk.Label(win, text="Sheet:").pack(anchor='w', padx=20, pady=(10,0))
        sheet_var = tk.StringVar(value=edge.get('excel_mapping', {}).get('sheet', ''))
        sheet_combo = ttk.Combobox(win, textvariable=sheet_var, 
                                   values=list(self.excel_columns.keys()), state='readonly')
        sheet_combo.pack(anchor='w', padx=20, fill='x', pady=5)
        
        # Column selection
        ttk.Label(win, text="Column:").pack(anchor='w', padx=20, pady=(10,0))
        column_var = tk.StringVar(value=edge.get('excel_mapping', {}).get('column', ''))
        column_combo = ttk.Combobox(win, textvariable=column_var)
        column_combo.pack(anchor='w', padx=20, fill='x', pady=5)
        
        # Update column list when sheet changes
        def on_sheet_change(*args):
            sheet = sheet_var.get()
            columns = self.excel_columns.get(sheet, [])
            column_combo['values'] = columns
        
        sheet_var.trace('w', on_sheet_change)
        on_sheet_change()
        
        # Save button
        def save_mapping():
            edge['excel_mapping'] = {
                'enabled': enabled_var.get(),
                'sheet': sheet_var.get(),
                'column': column_var.get()
            }
            win.destroy()
            self.refresh_tree()
            self.status_var.set("Mapping updated (not saved yet)")
        
        ttk.Button(win, text="Save Mapping", command=save_mapping).pack(pady=20)
    
    def auto_map_all(self):
        if messagebox.askyesno("Auto-Map", "Auto-map all unmapped flows?"):
            area_to_sheet = {
                'ug2n': 'Flows_UG2N',
                'mern': 'Flows_MERN',
                'mers': 'Flows_MERS',
                'merplant': 'Flows_MERP',
                'ug2s': 'Flows_UG2S',
                'ug2plant': 'Flows_UG2P',
                'oldtsf': 'Flows_OLDTSF',
                'stockpile': 'Flows_STOCKPILE'
            }
            
            count = 0
            for edge in self.edges:
                from_node = edge['from'].lower()
                to_node = edge['to'].lower()
                
                # Find area
                area = None
                for code, sheet in area_to_sheet.items():
                    if code in from_node:
                        area = code
                        break
                
                if not area:
                    continue
                
                sheet = area_to_sheet[area]
                if sheet not in self.excel_columns:
                    continue
                
                # Find matching column
                flow_name = f"{edge['from']}__TO__{edge['to']}".lower()
                columns = self.excel_columns[sheet]
                
                found = None
                for col in columns:
                    if col.lower() == flow_name or (edge['from'].lower() in col.lower() and edge['to'].lower() in col.lower()):
                        found = col
                        break
                
                if found:
                    edge['excel_mapping'] = {
                        'enabled': True,
                        'sheet': sheet,
                        'column': found
                    }
                    count += 1
            
            self.refresh_tree()
            messagebox.showinfo("Success", f"Auto-mapped {count} flows")
            self.status_var.set(f"Auto-mapped {count} flows (not saved yet)")
    
    def save_changes(self):
        try:
            self.data['edges'] = self.edges
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", "Changes saved to JSON!")
            self.status_var.set("All changes saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def browse_files(self):
        json_path = filedialog.askopenfilename(
            title="Select JSON diagram file",
            filetypes=[("JSON files", "*.json")]
        )
        if json_path:
            self.json_file = Path(json_path)
            self.load_data()

if __name__ == '__main__':
    root = tk.Tk()
    app = ExcelMappingManager(root)
    root.mainloop()
