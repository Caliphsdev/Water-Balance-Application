"""
Storage Facilities Management Module

This module provides a comprehensive interface for managing storage facilities:
- View all storage facilities (dams and tanks)
- Summary dashboard with key metrics
- Add new storage facilities
- Edit existing facilities
- Delete facilities
- Monitor capacity and current volume
- Track operating levels
- Search and filter functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from utils.config_manager import config
from database.db_manager import DatabaseManager


class StorageFacilitiesModule:
    """Storage Facilities Management Module"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.facilities = []
        self.facility_types = []
        self.filtered_facilities = []
        self.tree = None
        
        # Search/filter variables
        self.search_var = tk.StringVar()
        self.type_filter_var = tk.StringVar()
        self.status_filter_var = tk.StringVar()
        
        # Cache for Excel aggregation to avoid repeated loads
        self._excel_cache = None
        self._excel_cache_key = None
        
    def load(self):
        """Load the storage facilities module"""
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Main container with modern styling
        container = tk.Frame(self.parent, bg='#f5f6fa')
        container.pack(fill='both', expand=True)
        
        # Create sections
        self._create_header(container)
        self._create_summary_cards(container)
        self._create_toolbar(container)
        self._create_data_grid(container)
        
        # Load initial data
        self._load_data()
        
    def _create_header(self, parent):
        """Create modern header section"""
        header_frame = tk.Frame(parent, bg='#f5f6fa')
        header_frame.pack(fill='x', padx=25, pady=(25, 15))
        
        # Title with icon
        title_container = tk.Frame(header_frame, bg='#f5f6fa')
        title_container.pack(side='left', fill='x', expand=True)
        
        title = tk.Label(
            title_container,
            text="Storage Facilities",
            font=('Segoe UI', 28, 'bold'),
            fg='#2c3e50',
            bg='#f5f6fa',
            anchor='w'
        )
        title.pack(side='top', anchor='w')
        
        subtitle = tk.Label(
            title_container,
            text="Monitor and manage water storage infrastructure",
            font=('Segoe UI', 11),
            fg='#7f8c8d',
            bg='#f5f6fa',
            anchor='w'
        )
        subtitle.pack(side='top', anchor='w', pady=(2, 0))
        
        # Refresh button with modern style
        refresh_btn = tk.Button(
            header_frame,
            text="⟳ Refresh Data",
            font=('Segoe UI', 10, 'bold'),
            fg='white',
            bg='#3498db',
            activebackground='#2980b9',
            activeforeground='white',
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0,
            command=self._load_data
        )
        refresh_btn.pack(side='right')
        
        # Hover effect for refresh button
        def on_enter(e):
            refresh_btn.config(bg='#2980b9')
        def on_leave(e):
            refresh_btn.config(bg='#3498db')
        refresh_btn.bind('<Enter>', on_enter)
        refresh_btn.bind('<Leave>', on_leave)
        
    def _create_summary_cards(self, parent):
        """Create modern summary dashboard cards"""
        cards_frame = tk.Frame(parent, bg='#f5f6fa')
        cards_frame.pack(fill='x', padx=25, pady=(0, 15))
        
        # Calculate totals
        self.total_capacity_label = None
        self.total_volume_label = None
        self.utilization_label = None
        self.active_count_label = None
        
        # Card 1: Total Capacity
        card1 = self._create_card(cards_frame, '#3498db', '💧', 'Total Capacity', '0 m³')
        card1.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.total_capacity_label = card1
        
        # Card 2: Current Volume
        card2 = self._create_card(cards_frame, '#2ecc71', '📊', 'Current Volume', '0 m³')
        card2.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.total_volume_label = card2
        
        # Card 3: Average Utilization
        card3 = self._create_card(cards_frame, '#f39c12', '📈', 'Avg Utilization', '0%')
        card3.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.utilization_label = card3
        
        # Card 4: Active Facilities
        card4 = self._create_card(cards_frame, '#9b59b6', '✓', 'Active Facilities', '0')
        card4.pack(side='left', fill='both', expand=True)
        self.active_count_label = card4
        
    def _create_card(self, parent, color, icon, label, value):
        """Create a modern dashboard card"""
        card = tk.Frame(parent, bg='white', relief='flat', borderwidth=0)
        card.configure(highlightbackground='#e0e0e0', highlightthickness=1)
        
        # Colored accent bar
        accent = tk.Frame(card, bg=color, height=5)
        accent.pack(fill='x')
        
        content = tk.Frame(card, bg='white')
        content.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Icon and label row
        top_row = tk.Frame(content, bg='white')
        top_row.pack(fill='x')
        
        icon_label = tk.Label(
            top_row,
            text=icon,
            font=('Segoe UI', 24),
            bg='white',
            fg=color
        )
        icon_label.pack(side='left')
        
        label_text = tk.Label(
            top_row,
            text=label,
            font=('Segoe UI', 10),
            fg='#7f8c8d',
            bg='white',
            anchor='w'
        )
        label_text.pack(side='left', padx=(10, 0), anchor='w')
        
        # Value
        value_label = tk.Label(
            content,
            text=value,
            font=('Segoe UI', 20, 'bold'),
            fg='#2c3e50',
            bg='white',
            anchor='w'
        )
        value_label.pack(anchor='w', pady=(5, 0))
        
        # Store value label for updates
        card.value_label = value_label
        
        return card
        
    def _create_toolbar(self, parent):
        """Create modern toolbar with search, filters, and actions"""
        toolbar = tk.Frame(parent, bg='white', relief='flat')
        toolbar.configure(highlightbackground='#e0e0e0', highlightthickness=1)
        toolbar.pack(fill='x', padx=25, pady=(0, 15))
        
        # Left side - Search and filters
        left_frame = tk.Frame(toolbar, bg='white')
        left_frame.pack(side='left', fill='x', expand=True, padx=20, pady=15)
        
        # Search with icon
        search_container = tk.Frame(left_frame, bg='white')
        search_container.pack(side='left', padx=(0, 15))
        
        search_icon = tk.Label(
            search_container,
            text="🔍",
            font=('Segoe UI', 12),
            bg='white'
        )
        search_icon.pack(side='left', padx=(0, 5))
        
        search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            font=('Segoe UI', 10),
            width=25,
            relief='flat',
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        search_entry.pack(side='left')
        search_entry.configure(insertbackground='#2c3e50')
        
        # Type filter
        type_container = tk.Frame(left_frame, bg='white')
        type_container.pack(side='left', padx=(0, 15))
        
        type_label = tk.Label(
            type_container,
            text="Type:",
            font=('Segoe UI', 10),
            bg='white',
            fg='#7f8c8d'
        )
        type_label.pack(side='left', padx=(0, 5))
        
        self.type_combo = ttk.Combobox(
            type_container,
            textvariable=self.type_filter_var,
            font=('Segoe UI', 10),
            width=15,
            state='readonly'
        )
        self.type_combo.pack(side='left')
        
        # Status filter
        status_container = tk.Frame(left_frame, bg='white')
        status_container.pack(side='left')
        
        status_label = tk.Label(
            status_container,
            text="Status:",
            font=('Segoe UI', 10),
            bg='white',
            fg='#7f8c8d'
        )
        status_label.pack(side='left', padx=(0, 5))
        
        status_combo = ttk.Combobox(
            status_container,
            textvariable=self.status_filter_var,
            font=('Segoe UI', 10),
            width=12,
            state='readonly',
            values=['All', 'Active', 'Inactive']
        )
        status_combo.set('Active')  # Default to showing only active
        status_combo.pack(side='left')
        
        # Right side - Action buttons
        right_frame = tk.Frame(toolbar, bg='white')
        right_frame.pack(side='right', padx=20, pady=15)
        
        # Modern button style
        button_style = {
            'font': ('Segoe UI', 10, 'bold'),
            'relief': 'flat',
            'cursor': 'hand2',
            'borderwidth': 0,
            'padx': 18,
            'pady': 9
        }
        
        # Add button
        add_btn = tk.Button(
            right_frame,
            text="+ Add Facility",
            fg='white',
            bg='#2ecc71',
            activebackground='#27ae60',
            activeforeground='white',
            command=self._show_add_dialog,
            **button_style
        )
        add_btn.pack(side='left', padx=(0, 8))
        
        # Edit button
        edit_btn = tk.Button(
            right_frame,
            text="✎ Edit",
            fg='white',
            bg='#3498db',
            activebackground='#2980b9',
            activeforeground='white',
            command=self._show_edit_dialog,
            **button_style
        )
        edit_btn.pack(side='left', padx=(0, 8))
        
        # Delete button
        delete_btn = tk.Button(
            right_frame,
            text="✕ Delete",
            fg='white',
            bg='#e74c3c',
            activebackground='#c0392b',
            activeforeground='white',
            command=self._delete_facility,
            **button_style
        )
        delete_btn.pack(side='left')
        
        # Hover effects
        for btn in [add_btn, edit_btn, delete_btn]:
            active_bg = btn['activebackground']
            normal_bg = btn['bg']
            btn.bind('<Enter>', lambda e, b=btn, c=active_bg: b.config(bg=c))
            btn.bind('<Leave>', lambda e, b=btn, c=normal_bg: b.config(bg=c))
        
    def _create_data_grid(self, parent):
        """Create modern data grid with enhanced styling"""
        grid_container = tk.Frame(parent, bg='white', relief='flat')
        grid_container.configure(highlightbackground='#e0e0e0', highlightthickness=1)
        grid_container.pack(fill='both', expand=True, padx=25, pady=(0, 25))
        
        # Grid header
        grid_header = tk.Frame(grid_container, bg='#2c3e50', height=45)
        grid_header.pack(fill='x')
        grid_header.pack_propagate(False)
        
        header_label = tk.Label(
            grid_header,
            text="📋 Storage Facilities Overview",
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg='#2c3e50',
            anchor='w'
        )
        header_label.pack(side='left', padx=20)
        
        # Create Treeview with scrollbars
        tree_frame = tk.Frame(grid_container, bg='white')
        tree_frame.pack(fill='both', expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient='vertical')
        tree_scroll_y.pack(side='right', fill='y')
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')
        
        # Define columns with better organization
        columns = ('ID', 'Code', 'Name', 'Type', 'Capacity', 'Volume', 'Utilization', 'Surface Area', 'Status')
        
        # Custom style for Treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.Treeview',
                       background='white',
                       foreground='#2c3e50',
                       fieldbackground='white',
                       font=('Segoe UI', 10),
                       rowheight=35)
        style.configure('Custom.Treeview.Heading',
                       background='#ecf0f1',
                       foreground='#2c3e50',
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat')
        style.map('Custom.Treeview',
                 background=[('selected', '#3498db')],
                 foreground=[('selected', 'white')])
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode='extended',
            style='Custom.Treeview',
            height=12
        )
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Configure columns with modern widths and proper alignment
        column_config = {
            'ID': (50, 'center', 'center'),
            'Code': (120, 'w', 'w'),
            'Name': (250, 'w', 'w'),
            'Type': (100, 'center', 'center'),
            'Capacity': (130, 'e', 'e'),
            'Volume': (130, 'e', 'e'),
            'Utilization': (110, 'center', 'center'),
            'Surface Area': (130, 'e', 'e'),
            'Status': (90, 'center', 'center')
        }
        
        for col in columns:
            width, data_anchor, heading_anchor = column_config.get(col, (100, 'w', 'w'))
            self.tree.heading(col, text=col, anchor=heading_anchor)
            self.tree.column(col, width=width, anchor=data_anchor, minwidth=width)
        
        self.tree.pack(fill='both', expand=True, padx=1, pady=1)

        # Configure tags for visual styling
        self.tree.tag_configure('inactive', foreground='#95a5a6', font=('Segoe UI', 10))
        self.tree.tag_configure('active', foreground='#2c3e50', font=('Segoe UI', 10))
        self.tree.tag_configure('high_util', background='#ffe5e5')  # Over 80%
        self.tree.tag_configure('low_util', background='#fff3cd')   # Under 20%
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', lambda e: self._show_edit_dialog())
        
        # Register trace callbacks
        self.search_var.trace('w', lambda *args: self._apply_filters())
        self.type_filter_var.trace('w', lambda *args: self._apply_filters())
        self.status_filter_var.trace('w', lambda *args: self._apply_filters())
        
        # Footer with info
        footer = tk.Frame(grid_container, bg='#ecf0f1', height=40)
        footer.pack(fill='x')
        footer.pack_propagate(False)
        
        self.info_label = tk.Label(
            footer,
            text="",
            font=('Segoe UI', 9),
            fg='#7f8c8d',
            bg='#ecf0f1',
            anchor='w'
        )
        self.info_label.pack(side='left', padx=20, fill='x', expand=True)
        
    def _get_latest_year_month(self):
        """Get the latest year/month present in both Excel files."""
        try:
            from utils.excel_timeseries import get_default_excel_repo
            from utils.excel_timeseries_extended import get_extended_excel_repo
            repo1 = get_default_excel_repo()
            repo2 = get_extended_excel_repo()
            latest1 = repo1.get_latest_date()
            repo2._load()
            latest2 = None
            if repo2._storage_df is not None and not repo2._storage_df.empty:
                valid_dates = repo2._storage_df['Date'].dropna()
                if not valid_dates.empty:
                    latest2 = valid_dates.max().date()
            # Use the latest of both
            candidates = [d for d in [latest1, latest2] if d]
            if not candidates:
                return None, None
            latest = max(candidates)
            return latest.year, latest.month
        except Exception:
            return None, None

    def _aggregate_monthly_storage(self, year, month):
        """Aggregate all rows for each facility within the month from the extended Excel repo (with caching)."""
        cache_key = (year, month)
        
        # Return cached result if available
        if self._excel_cache_key == cache_key and self._excel_cache is not None:
            return self._excel_cache
        
        try:
            from utils.excel_timeseries_extended import get_extended_excel_repo
            repo = get_extended_excel_repo()
            repo._load()
            df = repo._storage_df
            if df is None or df.empty:
                return {}
            mask = (df['Date'].dt.year == year) & (df['Date'].dt.month == month)
            month_df = df[mask]
            # Group by Facility_Code and sum inflow/outflow/abstraction
            grouped = month_df.groupby('Facility_Code').agg({
                'Inflow_m3': 'sum',
                'Outflow_m3': 'sum',
                'Abstraction_m3': 'sum' if 'Abstraction_m3' in df.columns else 'first'
            }).reset_index()
            # Build dict
            result = {}
            for _, row in grouped.iterrows():
                result[row['Facility_Code']] = {
                    'inflow': float(row['Inflow_m3']) if pd.notna(row['Inflow_m3']) else 0.0,
                    'outflow': float(row['Outflow_m3']) if pd.notna(row['Outflow_m3']) else 0.0,
                    'abstraction': float(row['Abstraction_m3']) if 'Abstraction_m3' in row and pd.notna(row['Abstraction_m3']) else 0.0
                }
            
            # Cache the result
            self._excel_cache = result
            self._excel_cache_key = cache_key
            return result
        except Exception:
            return {}

    def _load_data(self):
        """Load storage facilities and update with current volumes from latest Excel month, aggregated."""
        try:
            # Load facility types
            self.facility_types = self.db.get_facility_types()
            type_names = ['All'] + [ft['type_name'] for ft in self.facility_types]
            self.type_combo['values'] = type_names
            if not self.type_filter_var.get():
                self.type_combo.set('All')
            
            # Load facilities (all, including inactive)
            self.facilities = self.db.get_storage_facilities(active_only=False)
            
            # Find latest year/month in both Excel files
            year, month = self._get_latest_year_month()
            if year and month:
                # Aggregate all rows for each facility in that month
                monthly_data = self._aggregate_monthly_storage(year, month)
                # Update facilities with aggregated Excel data
                for facility in self.facilities:
                    code = facility['facility_code']
                    if code in monthly_data:
                        # Use aggregated inflow/outflow for display
                        facility['current_volume'] = monthly_data[code]['inflow'] - monthly_data[code]['outflow']
            
            self.filtered_facilities = self.facilities.copy()
            
            # Update summary cards
            self._update_summary_cards()
            
            # Apply filters
            self._apply_filters()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            
    def _update_summary_cards(self):
        """Update the summary dashboard cards with current data"""
        total_capacity = sum(f['total_capacity'] or 0 for f in self.facilities if f['active'])
        total_volume = sum(f['current_volume'] or 0 for f in self.facilities if f['active'])
        active_count = sum(1 for f in self.facilities if f['active'])
        
        # Calculate average utilization
        facilities_with_data = [f for f in self.facilities if f['active'] and f['total_capacity'] and f['total_capacity'] > 0]
        if facilities_with_data:
            utilizations = [(f['current_volume'] or 0) / f['total_capacity'] * 100 for f in facilities_with_data]
            avg_util = sum(utilizations) / len(utilizations)
        else:
            avg_util = 0
        
        # Update cards
        if self.total_capacity_label:
            self.total_capacity_label.value_label.config(text=f"{total_capacity:,.0f} m³")
        if self.total_volume_label:
            self.total_volume_label.value_label.config(text=f"{total_volume:,.0f} m³")
        if self.utilization_label:
            self.utilization_label.value_label.config(text=f"{avg_util:.1f}%")
        if self.active_count_label:
            self.active_count_label.value_label.config(text=str(active_count))
            
    def _apply_filters(self):
        """Apply search and filter criteria"""
        search_text = self.search_var.get().lower()
        type_filter = self.type_filter_var.get()
        status_filter = self.status_filter_var.get()
        
        # Start with all facilities
        filtered = self.facilities.copy()
        
        # Apply search filter
        if search_text:
            filtered = [
                f for f in filtered
                if search_text in f['facility_code'].lower()
                or search_text in f['facility_name'].lower()
            ]
        
        # Apply type filter
        if type_filter and type_filter != 'All':
            filtered = [f for f in filtered if f['type_name'] == type_filter]
        
        # Apply status filter
        if status_filter and status_filter != 'All':
            is_active = status_filter == 'Active'
            filtered = [f for f in filtered if f['active'] == is_active]
        
        self.filtered_facilities = filtered
        self._populate_grid()
        
    def _populate_grid(self):
        """Populate the data grid with filtered facilities"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered facilities
        for fac in self.filtered_facilities:
            status = '✓ Active' if fac['active'] else '✕ Inactive'
            capacity = f"{fac['total_capacity']:,.0f}" if fac['total_capacity'] else "—"
            current_vol = f"{fac['current_volume']:,.0f}" if fac['current_volume'] else "—"
            surface_area = f"{fac['surface_area']:,.0f}" if fac['surface_area'] else "—"
            
            # Calculate utilization
            utilization = "—"
            util_pct = 0
            if fac['total_capacity'] and fac['total_capacity'] > 0 and fac['current_volume']:
                util_pct = (fac['current_volume'] / fac['total_capacity'] * 100)
                utilization = f"{util_pct:.1f}%"
            
            # Determine tags for styling
            tags = []
            if fac['active']:
                tags.append('active')
                if util_pct > 80:
                    tags.append('high_util')
                elif util_pct < 20 and util_pct > 0:
                    tags.append('low_util')
            else:
                tags.append('inactive')
            
            self.tree.insert('', 'end', values=(
                fac['facility_id'],
                fac['facility_code'],
                fac['facility_name'],
                fac['type_name'],
                capacity,
                current_vol,
                utilization,
                surface_area,
                status
            ), tags=tuple(tags))
        
        # Update info label
        total = len(self.facilities)
        filtered = len(self.filtered_facilities)
        active = sum(1 for f in self.filtered_facilities if f['active'])
        
        self.info_label.config(
            text=f"Showing {filtered} of {total} facilities  •  {active} active  •  "
                 f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
    def _show_add_dialog(self):
        """Show dialog to add a new storage facility"""
        dialog = FacilityDialog(self.parent, self.db, self.facility_types, mode='add')
        self.parent.wait_window(dialog.dialog)
        
        if dialog.result:
            self._load_data()
            
    def _show_edit_dialog(self):
        """Show dialog to edit selected storage facility"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a storage facility to edit")
            return
        
        # Get selected facility ID
        facility_id = self.tree.item(selection[0])['values'][0]
        facility = next((f for f in self.facilities if f['facility_id'] == facility_id), None)
        
        if facility:
            dialog = FacilityDialog(self.parent, self.db, self.facility_types, mode='edit', facility=facility)
            self.parent.wait_window(dialog.dialog)
            
            if dialog.result:
                self._load_data()
                
    def _delete_facility(self):
        """Delete selected storage facilities (multi-select)"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select one or more storage facilities to delete")
            return
        
        # Gather selected facility names and IDs for confirmation
        facility_names = [self.tree.item(item)['values'][2] for item in selection]
        facility_ids = [self.tree.item(item)['values'][0] for item in selection]
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the following facilities?\n\n" +
            "\n".join(facility_names) +
            "\n\nThis action cannot be undone."
        )
        if confirm:
            try:
                deleted = self.db.delete_storage_facilities(facility_ids)
                messagebox.showinfo("Success", f"Deleted {deleted} storage facilit{'y' if deleted==1 else 'ies'} successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete facilities: {str(e)}")
            self._load_data()


class FacilityDialog:
    """Dialog for adding/editing storage facilities"""
    
    def __init__(self, parent, db, facility_types, mode='add', facility=None):
        self.db = db
        self.facility_types = facility_types
        self.mode = mode
        self.facility = facility
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{'Edit' if mode == 'edit' else 'Add'} Storage Facility")
        self.dialog.geometry("650x950")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)

        # Defer grab_set until window is visible to avoid TclError: window not viewable
        def _defer_grab():
            try:
                if self.dialog.winfo_viewable():
                    self.dialog.grab_set()
                else:
                    # Try again shortly if not yet mapped
                    self.dialog.after(25, _defer_grab)
            except Exception:
                pass
        self.dialog.after(25, _defer_grab)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (650 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (950 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Form variables
        self.facility_code_var = tk.StringVar(value=facility['facility_code'] if facility else '')
        self.facility_name_var = tk.StringVar(value=facility['facility_name'] if facility else '')
        self.type_var = tk.StringVar(value=facility['type_name'] if facility else '')
        self.capacity_var = tk.StringVar(value=str(facility['total_capacity']) if facility and facility['total_capacity'] else '')
        self.current_volume_var = tk.StringVar(value=str(facility['current_volume']) if facility and facility['current_volume'] else '0')
        self.surface_area_var = tk.StringVar(value=str(facility['surface_area']) if facility and facility['surface_area'] else '')
        self.min_level_var = tk.StringVar(value=str(facility['minimum_operating_level']) if facility and facility['minimum_operating_level'] else '0')
        self.max_level_var = tk.StringVar(value=str(facility['maximum_operating_level']) if facility and facility['maximum_operating_level'] else '100')
        self.description_var = tk.StringVar(value=facility['description'] if facility and facility['description'] else '')
        self.is_active_var = tk.BooleanVar(value=facility['active'] if facility else True)
        # Evaporation participation flag (defaults to True if missing)
        self.evap_active_var = tk.BooleanVar(value=(facility.get('evap_active', 1) == 1) if facility else True)
        
        self._create_form()
        
    def _create_form(self):
        """Create form fields"""
        # Scrollable container
        canvas = tk.Canvas(self.dialog, bg='white')
        scrollbar = ttk.Scrollbar(self.dialog, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Form content
        container = tk.Frame(scrollable_frame, bg='white', padx=30, pady=20)
        container.pack(fill='both', expand=True)
        
        # Title
        title = tk.Label(
            container,
            text=f"{'Edit' if self.mode == 'edit' else 'Add New'} Storage Facility",
            font=config.get_font('heading_medium'),
            fg=config.get_color('primary'),
            bg='white'
        )
        title.pack(anchor='w', pady=(0, 20))
        
        # Basic Information Section
        section_label = tk.Label(
            container,
            text="📋 Basic Information",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        section_label.pack(fill='x', pady=(0, 10))
        
        # Basic fields
        basic_fields = [
            ("Facility Code*", self.facility_code_var, "e.g., INYONI, NDCD1, PLANT_RWD"),
            ("Facility Name*", self.facility_name_var, "Full name of the storage facility"),
        ]
        
        for label_text, var, placeholder in basic_fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Type dropdown
        self._create_type_field(container)
        
        # Capacity Section
        section_label = tk.Label(
            container,
            text="📊 Capacity & Volume",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        section_label.pack(fill='x', pady=(20, 10))
        
        capacity_fields = [
            ("Capacity (m³)*", self.capacity_var, "Total storage capacity in cubic meters"),
            ("Current Volume (m³)", self.current_volume_var, "Current water volume"),
            ("Surface Area (m²)", self.surface_area_var, "Surface area for evaporation calculations"),
        ]
        
        for label_text, var, placeholder in capacity_fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Operating Levels Section
        section_label = tk.Label(
            container,
            text="📏 Operating Levels",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        section_label.pack(fill='x', pady=(20, 10))
        
        level_fields = [
            ("Minimum Operating Level (m)", self.min_level_var, "Minimum safe operating level"),
            ("Maximum Operating Level (m)", self.max_level_var, "Maximum operating level"),
        ]
        
        for label_text, var, placeholder in level_fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Description
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
        if self.facility and self.facility.get('description'):
            desc_text.insert('1.0', self.facility['description'])
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

        # Evaporation participation checkbox
        evap_check = tk.Checkbutton(
            container,
            text="Include in evaporation & rainfall calculations",
            variable=self.evap_active_var,
            font=config.get_font('body'),
            bg='white'
        )
        evap_check.pack(anchor='w', pady=(0, 20))
        
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
            text="Facility Type*",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        label.pack(fill='x', pady=(10, 2))
        
        type_names = [ft['type_name'] for ft in self.facility_types]
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
        """Validate and save the storage facility"""
        # Validate required fields
        if not self.facility_code_var.get().strip():
            messagebox.showerror("Validation Error", "Facility Code is required")
            return
        
        if not self.facility_name_var.get().strip():
            messagebox.showerror("Validation Error", "Facility Name is required")
            return
        
        if not self.type_var.get():
            messagebox.showerror("Validation Error", "Facility Type is required")
            return
        
        # Validate capacity
        try:
            capacity = float(self.capacity_var.get())
            if capacity <= 0:
                messagebox.showerror("Validation Error", "Capacity must be greater than 0")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Capacity must be a number")
            return
        
        # Validate current volume (optional)
        current_volume = 0
        if self.current_volume_var.get().strip():
            try:
                current_volume = float(self.current_volume_var.get())
                if current_volume < 0:
                    messagebox.showerror("Validation Error", "Current Volume cannot be negative")
                    return
                if current_volume > capacity:
                    messagebox.showerror("Validation Error", "Current Volume cannot exceed Capacity")
                    return
            except ValueError:
                messagebox.showerror("Validation Error", "Current Volume must be a number")
                return
        
        # Validate surface area (optional)
        surface_area = None
        if self.surface_area_var.get().strip():
            try:
                surface_area = float(self.surface_area_var.get())
                if surface_area < 0:
                    messagebox.showerror("Validation Error", "Surface Area cannot be negative")
                    return
            except ValueError:
                messagebox.showerror("Validation Error", "Surface Area must be a number")
                return
        
        # Validate operating levels
        try:
            min_level = float(self.min_level_var.get())
            max_level = float(self.max_level_var.get())
            if min_level < 0 or max_level < 0:
                messagebox.showerror("Validation Error", "Operating levels cannot be negative")
                return
            if min_level >= max_level:
                messagebox.showerror("Validation Error", "Minimum level must be less than Maximum level")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Operating levels must be numbers")
            return
        
        # Prepare data
        data = {
            'facility_code': self.facility_code_var.get().strip().upper(),
            'facility_name': self.facility_name_var.get().strip(),
            'facility_type': self.type_var.get(),
            'total_capacity': capacity,
            'current_volume': current_volume,
            'surface_area': surface_area,
            'minimum_operating_level': min_level,
            'maximum_operating_level': max_level,
            'description': self.description_text.get('1.0', 'end-1c').strip() or None,
            'active': self.is_active_var.get(),
            'evap_active': 1 if self.evap_active_var.get() else 0
        }
        
        try:
            if self.mode == 'add':
                self.db.add_storage_facility(**data)
                messagebox.showinfo("Success", "Storage facility added successfully")
            else:
                self.db.update_storage_facility(self.facility['facility_id'], **data)
                messagebox.showinfo("Success", "Storage facility updated successfully")
            
            self.result = True
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
