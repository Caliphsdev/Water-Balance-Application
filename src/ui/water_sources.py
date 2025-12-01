"""
Water Sources Management Module

This module provides a comprehensive interface for managing water sources including:
- View all water sources in a data grid
- Add new water sources
- Edit existing water sources
- Delete water sources
- Search and filter functionality
- Export to Excel/CSV
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.config_manager import config
from database.db_manager import DatabaseManager


class WaterSourcesModule:
    """Water Sources Management Module"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.sources = []
        self.source_types = []
        self.filtered_sources = []
        self.tree = None
        
        # Search/filter variables
        self.search_var = tk.StringVar()
        self.type_filter_var = tk.StringVar()
        self.status_filter_var = tk.StringVar()
        
    def load(self):
        """Load the water sources module into the parent container"""
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Main container
        container = tk.Frame(self.parent, bg=config.get_color('bg_main'))
        container.pack(fill='both', expand=True)
        
        # Create sections
        self._create_header(container)
        self._create_toolbar(container)
        self._create_data_grid(container)
        
        # Load initial data
        self._load_data()
        
    def _create_header(self, parent):
        """Create header section"""
        header_frame = tk.Frame(parent, bg=config.get_color('bg_main'))
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Title
        title = tk.Label(
            header_frame,
            text="💧 Water Sources Management",
            font=config.get_font('heading_large'),
            fg=config.get_color('primary'),
            bg=config.get_color('bg_main'),
            anchor='w'
        )
        title.pack(side='left', fill='x', expand=True)
        
        # Refresh button
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 Refresh",
            font=config.get_font('body_small'),
            fg='white',
            bg=config.get_color('primary'),
            activebackground=config.get_color('primary_dark'),
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            command=self._load_data
        )
        refresh_btn.pack(side='right', padx=5)
        
    def _create_toolbar(self, parent):
        """Create toolbar with search, filters, and actions"""
        toolbar = tk.Frame(parent, bg='white', relief='solid', borderwidth=1)
        toolbar.pack(fill='x', padx=20, pady=(0, 10))
        
        # Left side - Search and filters
        left_frame = tk.Frame(toolbar, bg='white')
        left_frame.pack(side='left', fill='x', expand=True, padx=15, pady=10)
        
        # Search
        search_label = tk.Label(
            left_frame,
            text="🔍 Search:",
            font=config.get_font('body'),
            bg='white'
        )
        search_label.pack(side='left', padx=(0, 5))
        
        search_entry = tk.Entry(
            left_frame,
            textvariable=self.search_var,
            font=config.get_font('body'),
            width=25
        )
        search_entry.pack(side='left', padx=(0, 20))
        
        # Type filter
        type_label = tk.Label(
            left_frame,
            text="Type:",
            font=config.get_font('body'),
            bg='white'
        )
        type_label.pack(side='left', padx=(0, 5))
        
        self.type_combo = ttk.Combobox(
            left_frame,
            textvariable=self.type_filter_var,
            font=config.get_font('body'),
            width=15,
            state='readonly'
        )
        self.type_combo.pack(side='left', padx=(0, 20))
        
        # Status filter
        status_label = tk.Label(
            left_frame,
            text="Status:",
            font=config.get_font('body'),
            bg='white'
        )
        status_label.pack(side='left', padx=(0, 5))
        
        status_combo = ttk.Combobox(
            left_frame,
            textvariable=self.status_filter_var,
            font=config.get_font('body'),
            width=12,
            state='readonly',
            values=['All', 'Active', 'Inactive']
        )
        status_combo.set('All')
        status_combo.pack(side='left')
        
        # Right side - Action buttons
        right_frame = tk.Frame(toolbar, bg='white')
        right_frame.pack(side='right', padx=15, pady=10)
        
        # Add button
        add_btn = tk.Button(
            right_frame,
            text="➕ Add Source",
            font=config.get_font('body'),
            fg='white',
            bg=config.get_color('success'),
            activebackground=config.get_color('success'),
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            command=self._show_add_dialog
        )
        add_btn.pack(side='left', padx=5)
        
        # Edit button
        edit_btn = tk.Button(
            right_frame,
            text="✏️ Edit",
            font=config.get_font('body'),
            fg='white',
            bg=config.get_color('primary'),
            activebackground=config.get_color('primary_dark'),
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            command=self._show_edit_dialog
        )
        edit_btn.pack(side='left', padx=5)
        
        # Delete button
        delete_btn = tk.Button(
            right_frame,
            text="🗑️ Delete",
            font=config.get_font('body'),
            fg='white',
            bg=config.get_color('danger'),
            activebackground=config.get_color('danger'),
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            command=self._delete_source
        )
        delete_btn.pack(side='left', padx=5)
        
    def _create_data_grid(self, parent):
        """Create data grid with scrollbars"""
        grid_frame = tk.Frame(parent, bg='white', relief='solid', borderwidth=1)
        grid_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Create Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(grid_frame, orient='vertical')
        tree_scroll_y.pack(side='right', fill='y')
        
        tree_scroll_x = ttk.Scrollbar(grid_frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')
        
        # Define columns
        columns = ('ID', 'Code', 'Name', 'Type', 'Average Flow', 'Units', 'Reliability', 'Status')
        
        self.tree = ttk.Treeview(
            grid_frame,
            columns=columns,
            show='headings',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode='browse',
            height=15
        )
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Configure columns
        column_widths = {
            'ID': 50,
            'Code': 120,
            'Name': 250,
            'Type': 120,
            'Average Flow': 120,
            'Units': 80,
            'Reliability': 100,
            'Status': 80
        }
        
        for col in columns:
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=column_widths.get(col, 100), anchor='w')
        
        self.tree.pack(fill='both', expand=True)
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', lambda e: self._show_edit_dialog())
        
        # Now register trace callbacks after tree is created
        self.search_var.trace('w', lambda *args: self._apply_filters())
        self.type_filter_var.trace('w', lambda *args: self._apply_filters())
        self.status_filter_var.trace('w', lambda *args: self._apply_filters())
        
        # Info label
        self.info_label = tk.Label(
            parent,
            text="",
            font=config.get_font('body_small'),
            fg=config.get_color('text_secondary'),
            bg=config.get_color('bg_main'),
            anchor='w'
        )
        self.info_label.pack(fill='x', padx=20, pady=(0, 10))
        
    def _load_data(self):
        """Load water sources from database"""
        try:
            # Load full source types (needed for add/edit dialog choices)
            self.source_types = self.db.get_source_types()

            # Load sources
            self.sources = self.db.get_water_sources()
            # Exclude monitoring/static-only sources from management view
            self.sources = [s for s in self.sources if s.get('source_purpose','ABSTRACTION') in ('ABSTRACTION','DUAL_PURPOSE')]
            self.filtered_sources = self.sources.copy()

            # Populate type filter only with types actually present in displayed sources to avoid stray types (e.g. monitoring-only like PCD/STP)
            present_type_names = sorted({s['type_name'] for s in self.sources})
            type_names = ['All'] + present_type_names
            self.type_combo['values'] = type_names
            if not self.type_filter_var.get() or self.type_filter_var.get() not in type_names:
                self.type_combo.set('All')
            
            # Apply filters
            self._apply_filters()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            
    def _apply_filters(self):
        """Apply search and filter criteria"""
        search_text = self.search_var.get().lower()
        type_filter = self.type_filter_var.get()
        status_filter = self.status_filter_var.get()
        
        # Start with all sources
        filtered = self.sources.copy()
        
        # Apply search filter
        if search_text:
            filtered = [
                s for s in filtered
                if search_text in s['source_code'].lower()
                or search_text in s['source_name'].lower()
            ]
        
        # Apply type filter
        if type_filter and type_filter != 'All':
            filtered = [s for s in filtered if s['type_name'] == type_filter]
        
        # Apply status filter
        if status_filter and status_filter != 'All':
            is_active = status_filter == 'Active'
            filtered = [s for s in filtered if s['active'] == is_active]
        
        self.filtered_sources = filtered
        self._populate_grid()
        
    def _populate_grid(self):
        """Populate the data grid with filtered sources"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered sources
        for source in self.filtered_sources:
            status = 'Active' if source['active'] else 'Inactive'
            avg_flow = f"{source['average_flow_rate']:,.2f}" if source['average_flow_rate'] else "N/A"
            reliability = f"{source['reliability_factor']*100:.0f}%" if source['reliability_factor'] else "N/A"

            # Append purpose indicator to type for clarity if dual purpose
            type_display = source['type_name']
            if source.get('source_purpose') == 'DUAL_PURPOSE':
                type_display = f"{type_display} (Dual)"
            
            self.tree.insert('', 'end', values=(
                source['source_id'],
                source['source_code'],
                source['source_name'],
                type_display,
                avg_flow,
                source['flow_units'],
                reliability,
                status
            ))
        
        # Update info label
        total = len(self.sources)
        filtered = len(self.filtered_sources)
        self.info_label.config(
            text=f"Showing {filtered} of {total} water sources | "
                 f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    def _show_add_dialog(self):
        """Show dialog to add a new water source"""
        dialog = SourceDialog(self.parent, self.db, self.source_types, mode='add')
        self.parent.wait_window(dialog.dialog)
        
        if dialog.result:
            self._load_data()
            
    def _show_edit_dialog(self):
        """Show dialog to edit selected water source"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a water source to edit")
            return
        
        # Get selected source ID
        source_id = self.tree.item(selection[0])['values'][0]
        source = next((s for s in self.sources if s['source_id'] == source_id), None)
        
        if source:
            dialog = SourceDialog(self.parent, self.db, self.source_types, mode='edit', source=source)
            self.parent.wait_window(dialog.dialog)
            
            if dialog.result:
                self._load_data()
                
    def _delete_source(self):
        """Delete selected water source"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a water source to delete")
            return
        
        # Get selected source
        source_id = self.tree.item(selection[0])['values'][0]
        source_name = self.tree.item(selection[0])['values'][2]
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n\n{source_name}\n\n"
            f"This action cannot be undone."
        )
        
        if confirm:
            try:
                self.db.delete_water_source(source_id)
                messagebox.showinfo("Success", "Water source deleted successfully")
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete source: {str(e)}")


class SourceDialog:
    """Dialog for adding/editing water sources"""
    
    def __init__(self, parent, db, source_types, mode='add', source=None):
        self.db = db
        self.source_types = source_types
        self.mode = mode
        self.source = source
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{'Edit' if mode == 'edit' else 'Add'} Water Source")
        self.dialog.geometry("650x800")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (650 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (800 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Form variables
        self.source_code_var = tk.StringVar(value=source['source_code'] if source else '')
        self.source_name_var = tk.StringVar(value=source['source_name'] if source else '')
        self.type_var = tk.StringVar(value=source['type_name'] if source else '')
        self.avg_flow_var = tk.StringVar(value=str(source['average_flow_rate']) if source and source['average_flow_rate'] else '')
        self.units_var = tk.StringVar(value=source['flow_units'] if source else 'm³/month')
        self.reliability_var = tk.StringVar(value=str(source['reliability_factor']*100) if source and source['reliability_factor'] else '100')
        self.description_var = tk.StringVar(value=source['description'] if source and source['description'] else '')
        self.is_active_var = tk.BooleanVar(value=source['active'] if source else True)
        
        self._create_form()
        
    def _create_form(self):
        """Create form fields"""
        # Main container with scrollbar
        canvas = tk.Canvas(self.dialog, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dialog, orient='vertical', command=canvas.yview)
        container = tk.Frame(canvas, bg='white', padx=30, pady=20)
        
        # Configure canvas scrolling
        container.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=container, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Title
        title = tk.Label(
            container,
            text=f"{'Edit' if self.mode == 'edit' else 'Add New'} Water Source",
            font=config.get_font('heading_medium'),
            fg=config.get_color('primary'),
            bg='white'
        )
        title.pack(anchor='w', pady=(0, 20))
        
        # Form fields
        fields = [
            ("Source Code*", self.source_code_var, "e.g., KD, GDB1, NDUGW"),
            ("Source Name*", self.source_name_var, "Full name of the water source"),
        ]
        
        for label_text, var, placeholder in fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Type dropdown
        self._create_type_field(container)
        
        # Numeric fields
        numeric_fields = [
            ("Average Flow Rate", self.avg_flow_var, "e.g., 89167.33"),
            ("Flow Units", self.units_var, "e.g., m³/month, m³/day"),
            ("Reliability Factor (%)*", self.reliability_var, "0-100")
        ]
        
        for label_text, var, placeholder in numeric_fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Description (text area)
        desc_label = tk.Label(
            container,
            text="Description",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        desc_label.pack(fill='x', pady=(10, 2))
        
        desc_text = tk.Text(
            container,
            font=config.get_font('body'),
            height=4,
            wrap='word'
        )
        desc_text.pack(fill='x', pady=(0, 15))
        if self.source and self.source.get('description'):
            desc_text.insert('1.0', self.source['description'])
        self.description_text = desc_text
        
        # Active checkbox
        active_check = tk.Checkbutton(
            container,
            text="Active",
            variable=self.is_active_var,
            font=config.get_font('body'),
            bg='white'
        )
        active_check.pack(anchor='w', pady=(0, 20))
        
        # Required field note
        note = tk.Label(
            container,
            text="* Required fields",
            font=config.get_font('body_small'),
            fg=config.get_color('text_secondary'),
            bg='white',
            anchor='w'
        )
        note.pack(fill='x', pady=(0, 20))
        
        # Buttons - centered at bottom with padding
        btn_frame = tk.Frame(container, bg='white')
        btn_frame.pack(fill='x', pady=(20, 10))
        
        # Center container for buttons
        btn_center = tk.Frame(btn_frame, bg='white')
        btn_center.pack(anchor='center')
        
        cancel_btn = tk.Button(
            btn_center,
            text="Cancel",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg=config.get_color('bg_secondary'),
            activebackground=config.get_color('bg_secondary'),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.dialog.destroy
        )
        cancel_btn.pack(side='left', padx=5)
        
        save_btn = tk.Button(
            btn_center,
            text=f"{'Update' if self.mode == 'edit' else 'Save'}",
            font=config.get_font('body'),
            fg='white',
            bg=config.get_color('success'),
            activebackground=config.get_color('success'),
            activeforeground='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._save
        )
        save_btn.pack(side='left', padx=5)
        
    def _create_field(self, parent, label_text, var, placeholder):
        """Create a form field"""
        label = tk.Label(
            parent,
            text=label_text,
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        label.pack(fill='x', pady=(10, 2))
        
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=config.get_font('body')
        )
        entry.pack(fill='x', pady=(0, 5))
        
        # Placeholder hint
        hint = tk.Label(
            parent,
            text=placeholder,
            font=config.get_font('body_small'),
            fg=config.get_color('text_secondary'),
            bg='white',
            anchor='w'
        )
        hint.pack(fill='x', pady=(0, 10))
        
    def _create_type_field(self, parent):
        """Create type dropdown field"""
        label = tk.Label(
            parent,
            text="Source Type*",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        label.pack(fill='x', pady=(10, 2))
        
        type_names = [st['type_name'] for st in self.source_types]
        combo = ttk.Combobox(
            parent,
            textvariable=self.type_var,
            font=config.get_font('body'),
            state='readonly',
            values=type_names
        )
        combo.pack(fill='x', pady=(0, 15))
        
        if not self.type_var.get() and type_names:
            combo.set(type_names[0])
        
    def _save(self):
        """Validate and save the water source"""
        # Validate required fields
        if not self.source_code_var.get().strip():
            messagebox.showerror("Validation Error", "Source Code is required")
            return
        
        if not self.source_name_var.get().strip():
            messagebox.showerror("Validation Error", "Source Name is required")
            return
        
        if not self.type_var.get():
            messagebox.showerror("Validation Error", "Source Type is required")
            return
        
        # Validate reliability factor
        try:
            reliability = float(self.reliability_var.get())
            if reliability < 0 or reliability > 100:
                messagebox.showerror("Validation Error", "Reliability Factor must be between 0 and 100")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Reliability Factor must be a number")
            return
        
        # Validate average flow (optional)
        avg_flow = None
        if self.avg_flow_var.get().strip():
            try:
                avg_flow = float(self.avg_flow_var.get())
            except ValueError:
                messagebox.showerror("Validation Error", "Average Flow Rate must be a number")
                return
        
        # Get type ID
        type_id = next(
            (st['type_id'] for st in self.source_types if st['type_name'] == self.type_var.get()),
            None
        )
        
        # Prepare data
        data = {
            'source_code': self.source_code_var.get().strip().upper(),
            'source_name': self.source_name_var.get().strip(),
            'type_id': type_id,
            'average_flow_rate': avg_flow,
            'flow_units': self.units_var.get().strip(),
            'reliability_factor': reliability / 100,
            'description': self.description_text.get('1.0', 'end-1c').strip() or None,
            'active': self.is_active_var.get()
        }
        
        try:
            if self.mode == 'add':
                self.db.add_water_source(**data)
                messagebox.showinfo("Success", "Water source added successfully")
            else:
                self.db.update_water_source(self.source['source_id'], **data)
                messagebox.showinfo("Success", "Water source updated successfully")
            
            self.result = True
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
