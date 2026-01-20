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
from ui.mouse_wheel_support import enable_canvas_mousewheel, enable_text_mousewheel, enable_treeview_mousewheel


class StorageFacilitiesModule:
    """Storage Facilities Management Module"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.facilities = []
        self.facility_types = []
        self.filtered_facilities = []
        self.tree = None
        self.volume_source_text = "Current volume from database"
        
        # Search/filter variables - pass master widget to avoid 'too early to create variable' error
        self.search_var = tk.StringVar(master=self.parent)
        self.type_filter_var = tk.StringVar(master=self.parent)
        self.status_filter_var = tk.StringVar(master=self.parent)
        
        # Cache for Excel aggregation to avoid repeated loads
        self._excel_cache = None
        self._excel_cache_key = None
        
    def load(self):
        """Load the storage facilities module"""
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Main container with modern styling
        container = tk.Frame(self.parent, bg='#f5f6f7')
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
        header_frame = tk.Frame(parent, bg='#f5f6f7')
        header_frame.pack(fill='x', padx=25, pady=(25, 15))
        
        # Title with icon
        title_container = tk.Frame(header_frame, bg='#f5f6f7')
        title_container.pack(side='left', fill='x', expand=True)
        
        title = tk.Label(
            title_container,
            text="Storage Facilities",
            font=('Segoe UI', 28, 'bold'),
            fg='#2c3e50',
            bg='#f5f6f7',
            anchor='w'
        )
        title.pack(side='top', anchor='w')
        
        subtitle = tk.Label(
            title_container,
            text="Monitor and manage water storage infrastructure",
            font=('Segoe UI', 11),
            fg='#7f8c8d',
            bg='#f5f6f7',
            anchor='w'
        )
        subtitle.pack(side='top', anchor='w', pady=(2, 0))
        
        # Refresh button with modern style
        refresh_btn = tk.Button(
            header_frame,
            text="⟳ Refresh Data",
            font=('Segoe UI', 10, 'bold'),
            fg='white',
            bg='#0066cc',
            activebackground='#0052a3',
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
            refresh_btn.config(bg='#0052a3')
        def on_leave(e):
            refresh_btn.config(bg='#0066cc')
        refresh_btn.bind('<Enter>', on_enter)
        refresh_btn.bind('<Leave>', on_leave)
        
    def _create_summary_cards(self, parent):
        """Create modern summary dashboard cards"""
        cards_frame = tk.Frame(parent, bg='#f5f6f7')
        cards_frame.pack(fill='x', padx=25, pady=(0, 15))
        
        # Calculate totals
        self.total_capacity_label = None
        self.total_volume_label = None
        self.utilization_label = None
        self.active_count_label = None
        
        # Card 1: Total Capacity
        card1 = self._create_card(cards_frame, '#0066cc', '💧', 'Total Capacity', '0 m³')
        card1.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.total_capacity_label = card1
        
        # Card 2: Current Volume
        card2 = self._create_card(cards_frame, '#28a745', '📊', 'Current Volume', '0 m³')
        card2.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.total_volume_label = card2
        
        # Card 3: Average Utilization
        card3 = self._create_card(cards_frame, '#ff9800', '📈', 'Avg Utilization', '0%')
        card3.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.utilization_label = card3
        
        # Card 4: Active Facilities
        card4 = self._create_card(cards_frame, '#6c3fb5', '✓', 'Active Facilities', '0')
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
            bg='white',
            fg='#2c3e50'
        )
        search_entry.pack(side='left')
        search_entry.configure(insertbackground='#2c3e50')
        # Disable default right-click context menu
        search_entry.bind('<Button-3>', lambda e: 'break')
        
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
        status_combo.set('All')  # Default to showing all facilities
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
            bg='#28a745',
            activebackground='#1f7e34',
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
            bg='#0066cc',
            activebackground='#0052a3',
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
            bg='#cc3333',
            activebackground='#aa2222',
            activeforeground='white',
            command=self._delete_facility,
            **button_style
        )
        delete_btn.pack(side='left', padx=(0, 8))
        
        # Monthly Parameters button
        params_btn = tk.Button(
            right_frame,
            text="📅 Monthly Params",
            fg='white',
            bg='#6c3fb5',
            activebackground='#5a2f95',
            activeforeground='white',
            command=self._show_monthly_params_dialog,
            **button_style
        )
        params_btn.pack(side='left')
        
        # Hover effects
        for btn in [add_btn, edit_btn, delete_btn, params_btn]:
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

        # Brief helper text for utilization and monthly roll-forward behavior
        helper_label = tk.Label(
            grid_header,
            text="Utilization = current volume ÷ capacity. End-of-month volume rolls into the next month per facility; it only moves when an explicit inter-facility transfer is defined.",
            font=('Segoe UI', 9),
            fg='white',
            bg='#2c3e50',
            anchor='w',
            wraplength=680,
            justify='left'
        )
        helper_label.pack(side='right', padx=16)
        
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
                       background='#c5d3e6',
                       foreground='#2c3e50',
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat')
        style.map('Custom.Treeview',
                 background=[('selected', '#0066cc')],
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
        enable_treeview_mousewheel(self.tree)
        
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
        footer = tk.Frame(grid_container, bg='#e8eef5', height=40)
        footer.pack(fill='x')
        footer.pack_propagate(False)
        
        self.info_label = tk.Label(
            footer,
            text="",
            font=('Segoe UI', 9),
            fg='#7f8c8d',
            bg='#e8eef5',
            anchor='w'
        )
        self.info_label.pack(side='left', padx=20, fill='x', expand=True)
        
    def _get_latest_year_month(self):
        """Get the latest year/month present in Meter Readings Excel."""
        try:
            from utils.excel_timeseries import get_default_excel_repo
            repo1 = get_default_excel_repo()
            latest1 = repo1.get_latest_date()
            # Extended Excel sheets removed (Excel now contains only Flow Diagram data)
            if latest1 is None:
                return None, None
            return latest1.year, latest1.month
        except Exception:
            return None, None

    def _aggregate_monthly_storage(self, year, month):
        """Aggregate all rows for each facility within the month from the extended Excel repo (with caching)."""
        cache_key = (year, month)
        
        # Return cached result if available
        if self._excel_cache_key == cache_key and self._excel_cache is not None:
            return self._excel_cache
        
        try:
            # Extended Excel sheets removed (Excel now contains only Flow Diagram data)
            # Return empty cache as extended storage data no longer available
            if True:  # Bypass extended Excel code
                return {}
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
            
            # Load facilities (all, including inactive) - force cache bypass for fresh data
            self.facilities = self.db.get_storage_facilities(active_only=False, use_cache=False)
            
            # Determine the freshest calc date already persisted
            calc_dates = []
            for facility in self.facilities:
                raw_date = facility.get('volume_calc_date')
                parsed_date = None
                if isinstance(raw_date, datetime):
                    parsed_date = raw_date.date()
                elif isinstance(raw_date, date):
                    parsed_date = raw_date
                elif isinstance(raw_date, str):
                    try:
                        parsed_date = datetime.fromisoformat(raw_date).date()
                    except ValueError:
                        parsed_date = None
                if parsed_date:
                    calc_dates.append(parsed_date)

            latest_calc_date = max(calc_dates) if calc_dates else None

            # Find latest year/month in both Excel files for gap-fill
            year = month = None
            monthly_data = {}
            year, month = self._get_latest_year_month()
            if year and month:
                monthly_data = self._aggregate_monthly_storage(year, month)

            # Fill only facilities without a persisted calc-date volume
            if monthly_data:
                for facility in self.facilities:
                    if facility.get('volume_calc_date'):
                        continue
                    code = facility['facility_code']
                    if code in monthly_data:
                        facility['current_volume'] = (
                            monthly_data[code]['inflow'] - monthly_data[code]['outflow']
                        )

            # Record source for footer messaging
            if latest_calc_date and monthly_data:
                self.volume_source_text = (
                    f"Calc volumes ({latest_calc_date:%Y-%m-%d}); "
                    f"gaps filled with Excel {year}-{month:02d}"
                )
            elif latest_calc_date:
                self.volume_source_text = f"Calc volumes ({latest_calc_date:%Y-%m-%d})"
            elif monthly_data and year and month:
                self.volume_source_text = (
                    f"Excel volumes {year}-{month:02d} (inflow - outflow)"
                )
            else:
                self.volume_source_text = "Volumes from database (no calc date or Excel data)"
            
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
            text=(
                f"Showing {filtered} of {total} facilities  •  {active} active  •  "
                f"{self.volume_source_text}  •  "
                f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
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

    def _show_monthly_params_dialog(self):
        """Show dialog to configure monthly rainfall and evaporation"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a storage facility")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Multiple Selection", "Please select one facility at a time")
            return
        
        try:
            facility_id = self.tree.item(selection[0])['values'][0]
            # Get facility details
            facility = self.db.get_storage_facility(facility_id)
            if facility:
                FacilityMonthlyParamsDialog(self.parent, self.db, facility)
                self._load_data()  # Refresh after potential changes
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open monthly parameters: {str(e)}")


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
        
        # Make dialog responsive to screen size
        screen_height = parent.winfo_screenheight()
        dialog_width = 900
        dialog_height = min(700, int(screen_height * 0.85))  # Max 700px or 85% of screen height
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
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
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (dialog_width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Form variables
        self.facility_code_var = tk.StringVar(value=facility['facility_code'] if facility else '')
        self.facility_name_var = tk.StringVar(value=facility['facility_name'] if facility else '')
        self.type_var = tk.StringVar(value=facility['type_name'] if facility else '')
        self.capacity_var = tk.StringVar(value=str(facility['total_capacity']) if facility and facility['total_capacity'] else '')
        self.current_volume_var = tk.StringVar(value=str(facility['current_volume']) if facility and facility['current_volume'] else '0')
        # Track if volume was set by calculation (read-only if true)
        self.volume_calc_date = facility.get('volume_calc_date') if facility else None
        self.surface_area_var = tk.StringVar(value=str(facility['surface_area']) if facility and facility['surface_area'] else '')
        self.pump_start_var = tk.StringVar(value=str(facility['pump_start_level']) if facility and facility['pump_start_level'] else '70')
        self.pump_stop_var = tk.StringVar(value=str(facility['pump_stop_level']) if facility and facility['pump_stop_level'] else '20')
        self.purpose_var = tk.StringVar(value=facility['purpose'] if facility and facility['purpose'] else 'raw_water')
        self.water_quality_var = tk.StringVar(value=facility['water_quality'] if facility and facility['water_quality'] else 'process')
        self.description_var = tk.StringVar(value=facility['description'] if facility and facility['description'] else '')
        self.is_active_var = tk.BooleanVar(value=facility['active'] if facility else True)
        self.evap_active_var = tk.BooleanVar(value=(facility.get('evap_active', 1) == 1) if facility else True)
        self.is_lined_var = tk.BooleanVar(value=(facility.get('is_lined', 0) == 1) if facility else False)
        
        self._create_form()
        
    def _create_form(self):
        """Create form fields"""
        # Main container with scrollable area and fixed button area
        main_container = tk.Frame(self.dialog, bg='white')
        main_container.pack(fill='both', expand=True)
        
        # Scrollable container for form content
        scroll_container = tk.Frame(main_container, bg='white')
        scroll_container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(scroll_container, bg='white')
        scrollbar = ttk.Scrollbar(scroll_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Fixed button area at bottom (outside scrollable area)
        button_container = tk.Frame(main_container, bg='white', relief='solid', borderwidth=1)
        button_container.pack(fill='x', side='bottom', pady=0)
        
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
        
        # Warning if volume was set by calculation (editable but with notice)
        if self.volume_calc_date and self.mode == 'edit':
            warning_frame = tk.Frame(container, bg='#FFF3CD', relief='solid', borderwidth=1)
            warning_frame.pack(fill='x', pady=(0, 10))
            warning_icon = tk.Label(
                warning_frame,
                text="⚠️",
                font=('Segoe UI', 12),
                bg='#FFF3CD',
                fg='#856404'
            )
            warning_icon.pack(side='left', padx=(10, 5), pady=8)
            warning_text = tk.Label(
                warning_frame,
                text=f"Current Volume was set by calculation on {self.volume_calc_date}. Manual edits will break the monthly volume chain and require recalculation of subsequent months.",
                font=config.get_font('body_small'),
                bg='#FFF3CD',
                fg='#856404',
                wraplength=700,
                justify='left'
            )
            warning_text.pack(side='left', padx=(0, 10), pady=8)
        
        for label_text, var, placeholder in capacity_fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Pump & Alarm Controls Section (Industry standard)
        section_label = tk.Label(
            container,
            text="⚙️ Pump & Alarm Controls",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        section_label.pack(fill='x', pady=(20, 10))
        
        pump_fields = [
            ("Pump Start Level (%)", self.pump_start_var, "Begin pumping when dam reaches this level (e.g., 70%)"),
            ("Pump Stop Level (%)", self.pump_stop_var, "Stop pumping when dam drops to this level (e.g., 20%, protects pump from cavitation)"),
        ]
        
        for label_text, var, placeholder in pump_fields:
            self._create_field(container, label_text, var, placeholder)
        
        # Water Classification Section
        section_label = tk.Label(
            container,
            text="💧 Water Classification",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        section_label.pack(fill='x', pady=(20, 10))
        
        # Purpose dropdown
        purpose_label = tk.Label(
            container,
            text="Purpose",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        purpose_label.pack(fill='x', pady=(10, 2))
        
        purpose_combo = ttk.Combobox(
            container,
            textvariable=self.purpose_var,
            font=config.get_font('body'),
            state='readonly',
            values=['raw_water', 'return_water', 'storm_water', 'clean_water']
        )
        purpose_combo.pack(fill='x', pady=(0, 15))
        
        # Water quality dropdown
        quality_label = tk.Label(
            container,
            text="Water Quality",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        quality_label.pack(fill='x', pady=(10, 2))
        
        quality_combo = ttk.Combobox(
            container,
            textvariable=self.water_quality_var,
            font=config.get_font('body'),
            state='readonly',
            values=['potable', 'process', 'contaminated']
        )
        quality_combo.pack(fill='x', pady=(0, 15))
        
        # Pump Connections Section
        conn_section_label = tk.Label(
            container,
            text="⚙️ Pump Connections (Auto-Transfer Routes)",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        conn_section_label.pack(fill='x', pady=(20, 10))
        
        conn_hint = tk.Label(
            container,
            text="Define destination facilities for automatic transfers when this facility reaches pump start level (↓). Transfers occur in priority order, skipping full dams.",
            font=config.get_font('body_small'),
            fg=config.get_color('text_secondary'),
            bg='white',
            anchor='w',
            wraplength=500,
            justify='left'
        )
        conn_hint.pack(fill='x', pady=(0, 10))
        
        # Connections list frame (scrollable)
        conn_frame = tk.Frame(container, bg='white', relief='solid', borderwidth=1)
        conn_frame.pack(fill='both', expand=False, pady=(0, 15))
        
        # Create placeholder for connections
        self.connections_frame = conn_frame
        self.connections_list = []  # Will store connection widgets
        self._load_connections_ui()
        
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
        enable_text_mousewheel(desc_text)
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
        evap_check.pack(anchor='w', pady=(0, 5))

        # Lined facility checkbox
        lined_check = tk.Checkbutton(
            container,
            text="Lined facility (reduces seepage loss)",
            variable=self.is_lined_var,
            font=config.get_font('body'),
            bg='white'
        )
        lined_check.pack(anchor='w', pady=(0, 20))
        
        # Info label for seepage rates
        seepage_info = tk.Label(
            container,
            text="Seepage: Lined facilities = 0.1%/month, Unlined = 0.5%/month (editable in Settings > Constants)",
            font=config.get_font('body_small'),
            fg=config.get_color('text_secondary'),
            bg='white',
            anchor='w'
        )
        seepage_info.pack(fill='x', pady=(0, 20))
        
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
        
        # Buttons - in fixed container at bottom (created earlier, now populate it)
        # Center container for buttons
        btn_center = tk.Frame(button_container, bg='white')
        btn_center.pack(anchor='center', pady=15)
        
        cancel_btn = tk.Button(
            btn_center,
            text="Cancel",
            font=config.get_font('body'),
            fg='white',
            bg='#424242',
            activebackground='#616161',
            activeforeground='white',
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
        
    def _load_connections_ui(self):
        """Load and display facility connections for pump transfers"""
        # Clear existing connections
        for widget in self.connections_frame.winfo_children():
            widget.destroy()
        self.connections_list = []
        
        # Get all active facilities except current one
        all_facilities = self.db.get_storage_facilities()
        current_code = self.facility_code_var.get().strip().upper()
        available_facilities = [
            f for f in all_facilities 
            if f.get('active') == 1 and f['facility_code'].upper() != current_code
        ]
        
        if not available_facilities:
            empty_label = tk.Label(
                self.connections_frame,
                text="No other active facilities available for connections",
                font=config.get_font('body_small'),
                fg=config.get_color('text_secondary'),
                bg='white',
                padx=10,
                pady=10
            )
            empty_label.pack()
            return
        
        # Parse current connections from feeds_to if available
        current_feeds = ""
        if self.facility and self.facility.get('feeds_to'):
            current_feeds = self.facility['feeds_to']
        
        current_connections = [c.strip() for c in current_feeds.split(',') if c.strip()]
        
        # Create scrollable container for connections
        canvas = tk.Canvas(self.connections_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.connections_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
        
        # Add existing connections first
        for idx, conn_code in enumerate(current_connections):
            self._create_connection_row(scrollable_frame, conn_code, available_facilities, idx)
        
        # Add button to add more connections
        add_btn_frame = tk.Frame(self.connections_frame, bg='white')
        add_btn_frame.pack(fill='x', padx=5, pady=5)
        
        add_conn_btn = tk.Button(
            add_btn_frame,
            text="+ Add Connection",
            font=config.get_font('body'),
            fg='white',
            bg=config.get_color('primary'),
            activebackground=config.get_color('secondary'),
            relief='flat',
            padx=10,
            pady=5,
            cursor='hand2',
            command=lambda: self._create_connection_row(scrollable_frame, "", available_facilities, len(self.connections_list))
        )
        add_conn_btn.pack(anchor='w')
        
        # Store reference for saving
        self.connections_frame.scrollable_frame = scrollable_frame
    
    def _create_connection_row(self, parent, current_code, available_facilities, index):
        """Create a connection row with dropdown and remove button"""
        row = tk.Frame(parent, bg='#f5f6fa', relief='solid', borderwidth=1)
        row.pack(fill='x', pady=2, padx=2)
        
        # Priority number
        priority_label = tk.Label(
            row,
            text=f"{index + 1}.",
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='#f5f6fa',
            width=3
        )
        priority_label.pack(side='left', padx=(5, 10), pady=5)
        
        # Facility dropdown
        facility_var = tk.StringVar(value=current_code)
        facility_options = [f['facility_code'] for f in available_facilities]
        
        facility_combo = ttk.Combobox(
            row,
            textvariable=facility_var,
            font=config.get_font('body'),
            state='readonly',
            values=facility_options,
            width=20
        )
        facility_combo.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        # Remove button
        remove_btn = tk.Button(
            row,
            text="✕",
            font=config.get_font('body_small'),
            fg='white',
            bg='#e74c3c',
            activebackground='#c0392b',
            relief='flat',
            width=3,
            cursor='hand2',
            command=lambda: self._remove_connection(row)
        )
        remove_btn.pack(side='right', padx=5, pady=5)
        
        # Store reference
        row.facility_var = facility_var
        self.connections_list.append(row)
    
    def _remove_connection(self, row):
        """Remove a connection row"""
        row.destroy()
        self.connections_list.remove(row)
        
    def _save(self):
        """Validate and save the storage facility"""
        # Check if user is changing a calculated volume
        if self.volume_calc_date and self.mode == 'edit':
            original_volume = float(self.facility['current_volume']) if self.facility.get('current_volume') else 0
            try:
                new_volume = float(self.current_volume_var.get().strip()) if self.current_volume_var.get().strip() else 0
            except ValueError:
                new_volume = 0
            
            # If volume changed, show confirmation
            if abs(original_volume - new_volume) > 0.01:  # Allow for floating point tolerance
                from tkinter import messagebox
                result = messagebox.askyesno(
                    "Confirm Manual Override",
                    f"This facility's current volume was set by calculation on {self.volume_calc_date}.\\n\\n"
                    f"Changing from {original_volume:,.0f} m\u00b3 to {new_volume:,.0f} m\u00b3 will:\\n"
                    f"  \u2022 Break the monthly volume chain\\n"
                    f"  \u2022 Require recalculation of all subsequent months\\n"
                    f"  \u2022 Clear the calculation date\\n\\n"
                    f"Are you sure you want to manually override this calculated value?",
                    icon='warning'
                )
                if not result:
                    return  # User cancelled
                
                # Clear the calculation date since user is manually overriding
                # This will allow future calculations to use this manual value
                # Note: We'll set volume_calc_date=None in the update
        
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
        
        # Validate pump levels (percentages)
        try:
            pump_start = float(self.pump_start_var.get())
            pump_stop = float(self.pump_stop_var.get())
            if pump_start < 0 or pump_start > 100 or pump_stop < 0 or pump_stop > 100:
                messagebox.showerror("Validation Error", "Pump levels must be between 0 and 100%")
                return
            if pump_start <= pump_stop:
                messagebox.showerror("Validation Error", "Pump Start level must be greater than Pump Stop level")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Pump levels must be numbers (0-100)")
            return
        
        # Prepare data
        data = {
            'facility_code': self.facility_code_var.get().strip().upper(),
            'facility_name': self.facility_name_var.get().strip(),
            'facility_type': self.type_var.get(),
            'total_capacity': capacity,
            'current_volume': current_volume,
            'surface_area': surface_area,
            'pump_start_level': float(self.pump_start_var.get()),
            'pump_stop_level': float(self.pump_stop_var.get()),
            'purpose': self.purpose_var.get(),
            'water_quality': self.water_quality_var.get(),
            'description': self.description_text.get('1.0', 'end-1c').strip() or None,
            'active': self.is_active_var.get(),
            'evap_active': 1 if self.evap_active_var.get() else 0,
            'is_lined': 1 if self.is_lined_var.get() else 0
        }
        
        # If user manually changed a calculated volume, clear the calc date
        if self.volume_calc_date and self.mode == 'edit':
            original_volume = float(self.facility['current_volume']) if self.facility.get('current_volume') else 0
            if abs(original_volume - current_volume) > 0.01:
                data['volume_calc_date'] = None  # Clear calculation date on manual override
        
        # Collect connections in priority order
        connections = []
        for row in self.connections_list:
            conn_code = row.facility_var.get().strip()
            if conn_code:  # Only add non-empty selections
                connections.append(conn_code)
        
        if connections:
            data['feeds_to'] = ','.join(connections)
        else:
            data['feeds_to'] = None
        
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

class FacilityMonthlyParamsDialog:
    """Dialog for configuring monthly rainfall and evaporation per facility"""
    
    def __init__(self, parent, db, facility):
        self.db = db
        self.facility = facility
        self.facility_id = facility['facility_id']
        self.facility_code = facility['facility_code']
        
        # Monthly data caches (per-facility flows only)
        self.inflow_data = {}
        self.outflow_data = {}
        self.abstraction_data = {}
        self.inflow_entries = {}
        self.outflow_entries = {}
        self.abstraction_entries = {}
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Monthly Parameters: {self.facility_code}")
        self.dialog.geometry("900x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        
        # Defer grab_set
        def _defer_grab():
            try:
                if self.dialog.winfo_viewable():
                    self.dialog.grab_set()
                else:
                    self.dialog.after(25, _defer_grab)
            except Exception:
                pass
        self.dialog.after(25, _defer_grab)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (900 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_ui()
        self._load_data()
        
    def _create_ui(self):
        """Create tabbed interface for rainfall and evaporation"""
        # Header
        header_frame = tk.Frame(self.dialog, bg='#f5f6fa', relief='flat')
        header_frame.pack(fill='x', padx=0, pady=0)
        
        title = tk.Label(
            header_frame,
            text=f"Configure Monthly Flow Parameters for {self.facility_code}",
            font=('Segoe UI', 14, 'bold'),
            fg='#2c3e50',
            bg='#f5f6fa'
        )
        title.pack(padx=20, pady=15)
        
        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text="Set inflows, outflows, and abstraction (Rainfall & evaporation are regional)",
            font=('Segoe UI', 9),
            fg='#7f8c8d',
            bg='#f5f6fa'
        )
        subtitle.pack(padx=20, pady=(0, 10))
        
        # Modern tab styling with improved UX
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('StorageFacilitiesNotebook.TNotebook', background='#f5f6f7', borderwidth=0)
        # Enhanced tab styling: larger font, more padding for better visibility
        style.configure('StorageFacilitiesNotebook.TNotebook.Tab', 
                       background='#d6dde8', 
                       foreground='#2c3e50',
                       padding=[24, 16],  # Increased from [20, 12] for larger tab size
                       font=('Segoe UI', 11, 'bold'),  # Increased from 10 to 11, added bold
                       relief='flat',
                       borderwidth=0)
        # Enhanced map with better visual feedback on interaction
        style.map('StorageFacilitiesNotebook.TNotebook.Tab',
                 background=[('selected', '#3498db'), ('active', '#5dade2'), ('!active', '#d6dde8')],
                 foreground=[('selected', '#ffffff'), ('active', '#ffffff'), ('!active', '#2c3e50')],
                 lightcolor=[('selected', '#3498db')],
                 darkcolor=[('selected', '#3498db')])
        
        # Notebook (tabbed interface) with improved styling
        self.notebook = ttk.Notebook(self.dialog, style='StorageFacilitiesNotebook.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Tab 1: Inflow
        self._create_inflow_tab()
        
        # Tab 2: Outflow
        self._create_outflow_tab()
        
        # Tab 3: Abstraction
        self._create_abstraction_tab()
        
        # Bottom buttons
        button_frame = tk.Frame(self.dialog, bg='white')
        button_frame.pack(fill='x', padx=20, pady=15)
        
        save_btn = tk.Button(
            button_frame,
            text="💾 Save",
            font=('Segoe UI', 10, 'bold'),
            fg='white',
            bg='#28a745',
            activebackground='#1f7e34',
            relief='flat',
            padx=25,
            pady=10,
            command=self._save_data
        )
        save_btn.pack(side='right', padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="✕ Cancel",
            font=('Segoe UI', 10),
            fg='#7f8c8d',
            bg='#e8eef5',
            activeforeground='#7f8c8d',
            activebackground='#d9e6f4',
            relief='flat',
            padx=25,
            pady=10,
            command=self.dialog.destroy
        )
        cancel_btn.pack(side='right', padx=5)
        
    def _create_inflow_tab(self):
        """Create tab for monthly inflow configuration"""
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="💧 Inflow (m³)")
        
        # Scrollable grid
        canvas = tk.Canvas(tab, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        scrollbar.pack(side='right', fill='y')
        
        # Label
        label = tk.Label(
            scrollable_frame,
            text="Enter inflow in cubic meters (m³) for each month",
            font=('Segoe UI', 9),
            fg='#7f8c8d',
            bg='white'
        )
        label.pack(anchor='w', pady=(0, 15))
        
        # Month grid
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for idx, month in enumerate(months, 1):
            row_frame = tk.Frame(scrollable_frame, bg='white')
            row_frame.pack(fill='x', pady=5)
            
            month_label = tk.Label(
                row_frame,
                text=f"{month}:",
                font=('Segoe UI', 10),
                fg='#2c3e50',
                bg='white',
                width=6,
                anchor='w'
            )
            month_label.pack(side='left', padx=(0, 10))
            
            entry = tk.Entry(
                row_frame,
                font=('Segoe UI', 10),
                width=15,
                relief='solid',
                borderwidth=1
            )
            entry.pack(side='left', padx=5)
            self.inflow_entries[idx] = entry
            
            unit_label = tk.Label(
                row_frame,
                text="m³",
                font=('Segoe UI', 9),
                fg='#95a5a6',
                bg='white'
            )
            unit_label.pack(side='left', padx=5)
    
    def _create_outflow_tab(self):
        """Create tab for monthly outflow configuration"""
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="🚰 Outflow (m³)")
        
        # Scrollable grid
        canvas = tk.Canvas(tab, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        scrollbar.pack(side='right', fill='y')
        
        # Label
        label = tk.Label(
            scrollable_frame,
            text="Enter outflow in cubic meters (m³) for each month",
            font=('Segoe UI', 9),
            fg='#7f8c8d',
            bg='white'
        )
        label.pack(anchor='w', pady=(0, 15))
        
        # Month grid
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for idx, month in enumerate(months, 1):
            row_frame = tk.Frame(scrollable_frame, bg='white')
            row_frame.pack(fill='x', pady=5)
            
            month_label = tk.Label(
                row_frame,
                text=f"{month}:",
                font=('Segoe UI', 10),
                fg='#2c3e50',
                bg='white',
                width=6,
                anchor='w'
            )
            month_label.pack(side='left', padx=(0, 10))
            
            entry = tk.Entry(
                row_frame,
                font=('Segoe UI', 10),
                width=15,
                relief='solid',
                borderwidth=1
            )
            entry.pack(side='left', padx=5)
            self.outflow_entries[idx] = entry
            
            unit_label = tk.Label(
                row_frame,
                text="m³",
                font=('Segoe UI', 9),
                fg='#95a5a6',
                bg='white'
            )
            unit_label.pack(side='left', padx=5)
    
    def _create_abstraction_tab(self):
        """Create tab for monthly abstraction configuration"""
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="📤 Abstraction (m³)")
        
        # Scrollable grid
        canvas = tk.Canvas(tab, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        scrollbar.pack(side='right', fill='y')
        
        # Label
        label = tk.Label(
            scrollable_frame,
            text="Enter abstraction in cubic meters (m³) for each month",
            font=('Segoe UI', 9),
            fg='#7f8c8d',
            bg='white'
        )
        label.pack(anchor='w', pady=(0, 15))
        
        # Month grid
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for idx, month in enumerate(months, 1):
            row_frame = tk.Frame(scrollable_frame, bg='white')
            row_frame.pack(fill='x', pady=5)
            
            month_label = tk.Label(
                row_frame,
                text=f"{month}:",
                font=('Segoe UI', 10),
                fg='#2c3e50',
                bg='white',
                width=6,
                anchor='w'
            )
            month_label.pack(side='left', padx=(0, 10))
            
            entry = tk.Entry(
                row_frame,
                font=('Segoe UI', 10),
                width=15,
                relief='solid',
                borderwidth=1
            )
            entry.pack(side='left', padx=5)
            self.abstraction_entries[idx] = entry
            
            unit_label = tk.Label(
                row_frame,
                text="m³",
                font=('Segoe UI', 9),
                fg='#95a5a6',
                bg='white'
            )
            unit_label.pack(side='left', padx=5)
        

    def _load_data(self):
        """Load inflow, outflow, and abstraction data from DB"""
        try:
            # Load inflow
            self.inflow_data = self.db.get_facility_inflow_all_months(self.facility_id)
            for month, value in self.inflow_data.items():
                if month in self.inflow_entries:
                    self.inflow_entries[month].insert(0, str(value))
            
            # Load outflow
            self.outflow_data = self.db.get_facility_outflow_all_months(self.facility_id)
            for month, value in self.outflow_data.items():
                if month in self.outflow_entries:
                    self.outflow_entries[month].insert(0, str(value))
            
            # Load abstraction
            self.abstraction_data = self.db.get_facility_abstraction_all_months(self.facility_id)
            for month, value in self.abstraction_data.items():
                if month in self.abstraction_entries:
                    self.abstraction_entries[month].insert(0, str(value))
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        
    def _save_data(self):
        """Save inflow, outflow, and abstraction data to DB"""
        try:
            # Save inflow
            for month, entry in self.inflow_entries.items():
                value_str = entry.get().strip()
                if value_str:
                    try:
                        value = float(value_str)
                        self.db.set_facility_inflow_monthly(self.facility_id, month, value)
                    except ValueError:
                        messagebox.showwarning("Invalid Input", f"Month {month} inflow: please enter a number")
                        return
            
            # Save outflow
            for month, entry in self.outflow_entries.items():
                value_str = entry.get().strip()
                if value_str:
                    try:
                        value = float(value_str)
                        self.db.set_facility_outflow_monthly(self.facility_id, month, value)
                    except ValueError:
                        messagebox.showwarning("Invalid Input", f"Month {month} outflow: please enter a number")
                        return
            
            # Save abstraction
            for month, entry in self.abstraction_entries.items():
                value_str = entry.get().strip()
                if value_str:
                    try:
                        value = float(value_str)
                        self.db.set_facility_abstraction_monthly(self.facility_id, month, value)
                    except ValueError:
                        messagebox.showwarning("Invalid Input", f"Month {month} abstraction: please enter a number")
                        return
            
            messagebox.showinfo("Success", f"Monthly flow parameters saved for {self.facility_code}")
            self.dialog.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")