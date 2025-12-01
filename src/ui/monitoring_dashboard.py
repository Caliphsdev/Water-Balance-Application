"""Monitoring Dashboard Phase 1 Infrastructure
Category-separated monitoring views with sub-tabs (Stats, Charts, Data)
Filter panel skeleton and reusable placeholder components.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database.db_manager import DatabaseManager
from ui.data_import import DataImportModule
from utils.config_manager import config


class MonitoringDashboard:
    """Controller for monitoring data categories and sub-tabs."""

    CATEGORIES = [
        ("Static Level", "borehole_levels"),
        ("Groundwater Quality", "groundwater_quality"),
        ("Surface Water", "surface_water"),
        ("PCD", "pcd"),
        ("STP Effluent", "stp_effluent"),
    ]

    SUB_TABS = [
        ("Stats", "stats"),
        ("Charts", "charts"),
        ("Data", "data"),
    ]

    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.active_category = "borehole_levels"
        self.active_subtab = "stats"
        self.root_container = None
        self.filter_panel = None
        self.content_panel = None
        self.subtab_bar = None
        self.kpi_row = None
        self.alert_panel = None
        self.category_bar = None
        self.category_buttons = {}
        # Filter state
        self.selected_sites = []
        self.date_range = "Last 30d"
        self.date_from = None
        self.date_to = None
        self.selected_parameter = "Level"
        # Widget references
        self.date_range_cb = None
        self.site_listbox = None
        self.param_cb = None  # deprecated (parameter dropdown removed per new requirements)
        # Simple caches
        self._sites_cache = {}
        self._tab_frames = {}
        # Register DB listener for measurement-driven cache invalidation
        try:
            self.db.register_listener(self._on_db_event)
        except Exception:
            pass

    # -------- Public API --------
    def load(self):
        """Render full dashboard UI scaffolding."""
        self._reset()
        self._build_category_bar()
        self._build_body_layout()
        self._build_subtab_bar()
        self._render_active_view()

    # -------- Internal Layout Builders --------
    def _reset(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.root_container = tk.Frame(self.parent, bg=config.get_color('bg_main'))
        self.root_container.pack(fill='both', expand=True)

    def _build_category_bar(self):
        self.category_bar = tk.Frame(self.root_container, bg=config.get_color('bg_main'))
        self.category_bar.pack(fill='x', padx=16, pady=(16, 4))
        self.category_buttons.clear()
        for label, key in self.CATEGORIES:
            active = (key == self.active_category)
            btn = tk.Button(
                self.category_bar,
                text=label,
                font=config.get_font('body_bold') if active else config.get_font('body'),
                fg=config.get_color('text_primary') if active else config.get_color('text_secondary'),
                bg=config.get_color('bg_main'),
                relief='flat',
                padx=14, pady=6,
                cursor='hand2',
                command=lambda k=key: self._switch_category(k)
            )
            btn.pack(side='left', padx=(0, 10))
            self.category_buttons[key] = btn

    def _update_category_bar_styles(self):
        for label, key in self.CATEGORIES:
            btn = self.category_buttons.get(key)
            if not btn:
                continue
            active = (key == self.active_category)
            btn.configure(
                font=config.get_font('body_bold') if active else config.get_font('body'),
                fg=config.get_color('text_primary') if active else config.get_color('text_secondary')
            )

    def _build_body_layout(self):
        body = tk.Frame(self.root_container, bg=config.get_color('bg_main'))
        body.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        # Left filter panel
        self.filter_panel = tk.Frame(body, bg=config.get_color('bg_sidebar'), width=240)
        self.filter_panel.pack(side='left', fill='y')
        self.filter_panel.pack_propagate(False)
        self._build_filter_panel()
        # Main content area
        self.content_panel = tk.Frame(body, bg=config.get_color('bg_main'))
        self.content_panel.pack(side='left', fill='both', expand=True, padx=(16, 0))

    def _build_filter_panel(self):
        header = tk.Label(
            self.filter_panel,
            text="Filters",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_light'),
            bg=config.get_color('bg_sidebar'),
            anchor='w', padx=16, pady=12
        )
        header.pack(fill='x')
        # Date range
        tk.Label(self.filter_panel, text="Date Range", font=config.get_font('caption'), fg=config.get_color('text_light'), bg=config.get_color('bg_sidebar')).pack(anchor='w', padx=16, pady=(4,0))
        self.date_range_cb = ttk.Combobox(self.filter_panel, values=["Last 7d", "Last 30d", "YTD", "Custom"], state='readonly')
        self.date_range_cb.current(1)
        self.date_range_cb.pack(fill='x', padx=16, pady=(0,8))
        # Site selector placeholder
        tk.Label(self.filter_panel, text="Sites", font=config.get_font('caption'), fg=config.get_color('text_light'), bg=config.get_color('bg_sidebar')).pack(anchor='w', padx=16)
        site_frame = tk.Frame(self.filter_panel, bg=config.get_color('bg_sidebar'))
        site_frame.pack(fill='x', padx=16, pady=(0,8))
        self.site_listbox = tk.Listbox(site_frame, height=8, exportselection=False, selectmode='extended')
        self.site_listbox.pack(side='left', fill='both', expand=True)
        sb = tk.Scrollbar(site_frame, orient='vertical', command=self.site_listbox.yview)
        sb.pack(side='right', fill='y')
        self.site_listbox.configure(yscrollcommand=sb.set)
        # Populate category sites
        self._load_category_sites()
        # Parameter selector removed: parameters now displayed directly as table columns.
        # Apply button
        apply_btn = tk.Button(
            self.filter_panel, text="Apply", font=config.get_font('body_bold'), fg='white',
            bg=config.get_color('primary'), relief='flat', padx=12, pady=6,
            command=self._apply_filters
        )
        apply_btn.pack(padx=16, pady=(12,8), anchor='w')
        if self.active_category == 'borehole_levels':
            reset_btn = tk.Button(
                self.filter_panel, text="Reset Static Data", font=config.get_font('caption'), fg='white',
                bg='#9C27B0', relief='flat', padx=10, pady=4,
                command=self._reset_borehole_static_data
            )
            reset_btn.pack(padx=16, pady=(0,12), anchor='w')

    def _load_category_sites(self):
        """Populate site list based on active category mapping."""
        if not self.site_listbox:
            return
        self.site_listbox.delete(0, 'end')
        try:
            # Use cached list if available (category switch is frequent; data change is rare)
            if self.active_category in self._sites_cache:
                items = self._sites_cache[self.active_category]
            else:
                if self.active_category == 'borehole_levels':
                    rows = self.db.execute_query(
                        """
                        SELECT DISTINCT ws.source_name
                        FROM water_sources ws
                        JOIN measurements m ON ws.source_id = m.source_id
                        WHERE ws.source_purpose = 'MONITORING'
                          AND m.measurement_type = 'static_level'
                        ORDER BY ws.source_name
                        """
                    )
                elif self.active_category == 'groundwater_quality':
                    rows = self.db.execute_query(
                        """
                        SELECT DISTINCT ws.source_name
                        FROM water_sources ws
                        JOIN measurements m ON ws.source_id = m.source_id
                        WHERE ws.source_purpose = 'MONITORING'
                          AND m.measurement_type = 'quality_groundwater'
                        ORDER BY ws.source_name
                        """
                    )
                elif self.active_category == 'surface_water':
                    rows = self.db.execute_query(
                        """
                        SELECT DISTINCT ws.source_name
                        FROM water_sources ws
                        JOIN measurements m ON ws.source_id = m.source_id
                        WHERE m.measurement_type = 'quality_surface'
                          AND (ws.source_code NOT LIKE 'PCD%' AND ws.source_code NOT LIKE 'STP%')
                        ORDER BY ws.source_name
                        """
                    )
                elif self.active_category == 'pcd':
                    rows = self.db.execute_query(
                        """
                        SELECT DISTINCT ws.source_name
                        FROM water_sources ws
                        JOIN measurements m ON ws.source_id = m.source_id
                        WHERE m.measurement_type = 'quality_surface'
                          AND ws.source_code LIKE 'PCD%'
                        ORDER BY ws.source_name
                        """
                    )
                elif self.active_category == 'stp_effluent':
                    rows = self.db.execute_query(
                        """
                        SELECT DISTINCT ws.source_name
                        FROM water_sources ws
                        JOIN measurements m ON ws.source_id = m.source_id
                        WHERE m.measurement_type = 'quality_surface'
                          AND ws.source_code LIKE 'STP%'
                        ORDER BY ws.source_name
                        """
                    )
                else:
                    rows = []
                items = [r.get('source_name') for r in rows if r.get('source_name')]
                self._sites_cache[self.active_category] = items
            for it in items:
                self.site_listbox.insert('end', it)
        except Exception:
            pass

    def _get_category_parameters(self):
        """Derive parameter list dynamically from import template column definitions.
        Filters out identifier/date/notes columns and normalizes display names.
        """
        try:
            if not hasattr(self, '_template_param_cache'):
                dim = DataImportModule(self.parent, self.db)
                configs = dim.import_configs
                category_templates = {
                    # Option A: Borehole Levels shows ONLY static level.
                    'borehole_levels': ['static_level'],
                    'groundwater_quality': ['monitoring_borehole', 'groundwater_quality'],
                    'surface_water': ['surface_water_quality', 'river_monitoring'],
                    'pcd': ['pcd_physical', 'pcd_quality'],
                    'stp_effluent': ['stp_effluent']
                }
                cache = {}
                skip_tokens = {'measurement_date', 'notes'}
                code_suffixes = ('_code', 'source_code', 'borehole_code', 'pcd_code', 'river_code', 'plant_code', 'location_code')
                for cat, tmpl_keys in category_templates.items():
                    cols = []
                    for key in tmpl_keys:
                        conf = configs.get(key, {})
                        for col in conf.get('columns', []):
                            if col in skip_tokens or any(col.endswith(suf) for suf in code_suffixes):
                                continue
                            if col not in cols:
                                cols.append(col)
                    # Friendly names
                    friendly = []
                    for c in cols:
                        name = c
                        # strip common unit suffixes for display
                        for suf in ['_mgL', '_uScm', '_m', '_c', '_ntu']:
                            if name.endswith(suf):
                                name = name.replace(suf, '')
                        name = name.replace('_', ' ').title()
                        friendly.append(name)
                    cache[cat] = friendly
                # Override borehole_levels to emphasize level parameters first
                if 'borehole_levels' in cache:
                    level_order = []
                    for n in cache['borehole_levels']:
                        if 'Water Level' in n or 'Static Level' in n:
                            level_order.append(n)
                    others = [n for n in cache['borehole_levels'] if n not in level_order]
                    cache['borehole_levels'] = level_order + others
                self._template_param_cache = cache
            return self._template_param_cache.get(self.active_category, [])
        except Exception:
            # Fallback to previous static mapping if something fails
            fallback = {
                'borehole_levels': ["Water Level", "Static Level"],
                'groundwater_quality': ["pH", "EC", "TDS", "Nitrate"],
                'surface_water': ["pH", "EC", "Turbidity", "Sulphate"],
                'pcd': ["pH", "EC", "TDS", "Nitrate", "Sulphate"],
                'stp_effluent': ["pH", "Conductivity", "COD", "Nitrate"]
            }
            return fallback.get(self.active_category, [])

    def _build_subtab_bar(self):
        self.subtab_bar = tk.Frame(self.content_panel, bg=config.get_color('bg_main'))
        self.subtab_bar.pack(fill='x')
        for label, key in self.SUB_TABS:
            active = (key == self.active_subtab)
            btn = tk.Button(
                self.subtab_bar,
                text=label,
                font=config.get_font('body_bold') if active else config.get_font('body'),
                fg=config.get_color('text_primary') if active else config.get_color('text_secondary'),
                bg=config.get_color('bg_main'),
                relief='flat', padx=12, pady=6, cursor='hand2',
                command=lambda k=key: self._switch_subtab(k)
            )
            btn.pack(side='left', padx=(0, 8))
        sep = tk.Frame(self.content_panel, height=2, bg=config.get_color('divider'))
        sep.pack(fill='x', pady=(0,8))
        if not hasattr(self, '_content_area') or not self._content_area.winfo_exists():
            self._content_area = tk.Frame(self.content_panel, bg=config.get_color('bg_main'))
            self._content_area.pack(fill='both', expand=True)

    # -------- View Rendering --------
    def _render_active_view(self):
        # Hide existing tab frames
        for key, frame in list(self._tab_frames.items()):
            if frame.winfo_exists():
                frame.pack_forget()
        # Lazy build if needed
        if self.active_subtab not in self._tab_frames:
            if self.active_subtab == 'stats':
                frame = self._render_stats()
            elif self.active_subtab == 'charts':
                frame = self._render_charts()
            elif self.active_subtab == 'data':
                frame = self._render_data()
            else:
                frame = tk.Frame(self._content_area, bg=config.get_color('bg_main'))
            self._tab_frames[self.active_subtab] = frame
        # Show active frame
        active_frame = self._tab_frames[self.active_subtab]
        if active_frame.winfo_manager() == '':  # Not packed yet
            active_frame.pack(fill='both', expand=True)
        else:
            active_frame.pack(fill='both', expand=True)

    def _render_stats(self):
        frame = tk.Frame(self._content_area, bg=config.get_color('bg_main'))
        kpi_row = tk.Frame(frame, bg=config.get_color('bg_main'))
        kpi_row.pack(fill='x', pady=(0,12))
        # Placeholder KPIs per category
        kpis = self._get_placeholder_kpis()
        for label, value, accent in kpis:
            self._create_kpi_card(kpi_row, label, value, accent)
        # Placeholder summary table
        table_frame = tk.Frame(frame, bg='white', relief='solid', borderwidth=1)
        table_frame.pack(fill='both', expand=True)
        cols = ('Item', 'Detail', 'Severity')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=8)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=160, anchor='w')
        sample_rows = self._get_placeholder_alert_rows()
        for r in sample_rows:
            tree.insert('', 'end', values=r)
        tree.pack(fill='both', expand=True)
        return frame

    def _render_charts(self):
        frame = tk.Frame(self._content_area, bg=config.get_color('bg_main'))
        placeholder = tk.Label(
            frame,
            text=f"[Charts Placeholder: {self.active_category}]",
            font=config.get_font('body'),
            fg=config.get_color('text_secondary'),
            bg=config.get_color('bg_main')
        )
        placeholder.pack(pady=40)
        tk.Label(frame, text="Time Series / Distribution / Comparison coming in Phase 2", font=config.get_font('caption'), fg=config.get_color('text_secondary'), bg=config.get_color('bg_main')).pack()
        return frame

    def _render_data(self):
        frame = tk.Frame(self._content_area, bg=config.get_color('bg_main'))
        # Table
        table_frame = tk.Frame(frame, bg='white', relief='solid', borderwidth=1)
        table_frame.pack(fill='both', expand=True)
        columns, rows = self._get_placeholder_data_table()
        # Add horizontal + vertical scrollbars for wide parameter sets
        x_scroll = tk.Scrollbar(table_frame, orient='horizontal')
        y_scroll = tk.Scrollbar(table_frame, orient='vertical')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12,
                            xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.config(command=tree.xview)
        y_scroll.config(command=tree.yview)
        # Position scrollbars
        y_scroll.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
        x_scroll.pack(side='bottom', fill='x')
        col_width = max(120, int(self.content_panel.winfo_width() / max(1, len(columns))))
        for c in columns:
            tree.heading(c, text=c)
            tree.column(c, width=140 if c in ('Borehole','Site','Station','Dam','STP','Date') else 120, anchor='w', stretch=False)
        for r in rows:
            tree.insert('', 'end', values=r)
        # CRUD form removed until Phase 2 implementation.
        return frame

    # -------- Helpers / Data Placeholders --------
    def _create_kpi_card(self, parent, label, value, accent):
        card = tk.Frame(parent, bg='white', relief='solid', borderwidth=1)
        card.pack(side='left', padx=8, ipadx=10, ipady=8)
        tk.Label(card, text=label, font=config.get_font('caption'), fg=config.get_color('text_secondary'), bg='white').pack(anchor='w')
        tk.Label(card, text=value, font=config.get_font('heading_medium'), fg=accent, bg='white').pack(anchor='w')

    def _get_placeholder_kpis(self):
        if self.active_category == 'borehole_levels':
            # Hide KPIs entirely when no static level measurements exist
            try:
                count_rows = self.db.execute_query("SELECT COUNT(*) AS cnt FROM measurements WHERE measurement_type = 'static_level'")
                if not count_rows or count_rows[0].get('cnt', 0) == 0:
                    return []
                stats = self._compute_borehole_level_kpis()
                if stats.get('monitoring_count', 0) == 0:
                    return []
                return [
                    ("Monitoring Boreholes", str(stats['monitoring_count']), '#1E88E5'),
                    ("Up-to-Date %", f"{stats['uptodate_percent']}%", '#43A047'),
                    ("Declining", str(stats['declining_count']), '#E53935'),
                    ("Last Reading", stats['latest_reading'] or '—', '#6A1B9A')
                ]
            except Exception:
                return []
        # Other categories: empty until user imports data
        return []

    def _get_placeholder_alert_rows(self):
        # No alerts until data imported
        return []

    def _get_placeholder_data_table(self):
        # Generic dynamic column building based on template parameters
        params = self._get_category_parameters()  # friendly names
        if self.active_category == 'borehole_levels':
            base_label = 'Borehole'
        elif self.active_category == 'surface_water':
            base_label = 'Station'
        elif self.active_category == 'pcd':
            base_label = 'Dam'
        elif self.active_category == 'stp_effluent':
            base_label = 'STP'
        else:
            base_label = 'Borehole'
        cols = (base_label, 'Date') + tuple(params)
        rows = []
        try:
            if self.active_category == 'borehole_levels':
                raw_rows = self._fetch_borehole_static_filtered_table()
                for rr in raw_rows:
                    data_map = {'Static Level': rr[2]}
                    param_values = [data_map.get(p, '') for p in params]
                    rows.append((rr[0], rr[1]) + tuple(param_values))
            elif self.active_category in ('groundwater_quality','surface_water','pcd','stp_effluent'):
                quality_rows = self._fetch_quality_category_rows()
                for q in quality_rows:
                    site = q['site_label']
                    date = q['measurement_date']
                    data_map = q['values']  # already friendly-keyed
                    param_values = [data_map.get(p, '') for p in params]
                    rows.append((site, date) + tuple(param_values))
        except Exception:
            pass
        return cols, rows

    # -------- Interaction Handlers --------
    def _switch_category(self, key):
        if key == self.active_category:
            return
        self.active_category = key
        self.active_subtab = 'stats'
        # Refresh just the category button styles instead of full reload
        self._update_category_bar_styles()
        # Refresh sites list (cached) and subtab bar + view
        self._load_category_sites()
        self._rebuild_subtab_bar()
        self._tab_frames.clear()
        self._render_active_view()

    def _rebuild_subtab_bar(self):
        if self.subtab_bar:
            # Destroy existing subtab bar and following separator (second child)
            children = self.content_panel.winfo_children()
            for w in children[:2]:  # bar + separator
                w.destroy()
        self._build_subtab_bar()

    def _switch_subtab(self, key):
        if key != self.active_subtab:
            self.active_subtab = key
            self._render_active_view()

    def _apply_filters(self):
        # Update internal filter state from UI widgets then refresh current view.
        try:
            if self.date_range_cb:
                self.date_range = self.date_range_cb.get() or self.date_range
            # Selected sites
            if self.site_listbox:
                selections = self.site_listbox.curselection()
                self.selected_sites = [self.site_listbox.get(i) for i in selections]
            # Derive date_from based on date_range selection
            self.date_from, self.date_to = self._derive_date_bounds(self.date_range)
        except Exception:
            pass
        self._tab_frames.clear()
        self._render_active_view()

    def _on_db_event(self, event_type, payload):
        """Database event hook to invalidate caches lazily."""
        if event_type == 'measurement_added':
            self._sites_cache.clear()
            # Only clear stats/data frames; charts are placeholders
            for key in ['stats', 'data']:
                if key in self._tab_frames:
                    try:
                        self._tab_frames[key].destroy()
                    except Exception:
                        pass
                    self._tab_frames.pop(key, None)
            if self.active_subtab == 'stats':
                self._render_active_view()

    # -------- Real Data Wiring (Phase 2 Borehole Levels) --------
    def _compute_borehole_level_kpis(self):
        """Compute borehole level KPIs using measurements and water_sources.
        Logic:
                    - monitoring_count: count of sources with purpose MONITORING
          - uptodate_percent: % with a reading in last 30 days
          - declining_count: sources whose latest water_level_m dropped > threshold vs previous reading
          - latest_reading: most recent measurement_date across monitoring sources
        """
        thirty_days_ago_ord = datetime.now().date().toordinal() - 30
        try:
            rows = self.db.execute_query(
                """
                WITH ranked AS (
                    SELECT ws.source_id, ws.source_name,
                           m.measurement_date, m.water_level_m,
                           ROW_NUMBER() OVER (PARTITION BY ws.source_id ORDER BY m.measurement_date DESC) AS rn,
                           LEAD(m.water_level_m) OVER (PARTITION BY ws.source_id ORDER BY m.measurement_date DESC) AS prev_level
                    FROM water_sources ws
                    LEFT JOIN measurements m ON m.source_id = ws.source_id AND m.water_level_m IS NOT NULL
                    WHERE ws.source_purpose = 'MONITORING'
                )
                SELECT * FROM ranked WHERE rn = 1
                """
            )
            monitoring_count = len(rows)
            if monitoring_count == 0:
                return {
                    'monitoring_count': 0,
                    'uptodate_percent': 0,
                    'declining_count': 0,
                    'latest_reading': None
                }
            uptodate = 0
            declining = 0
            latest_dates = []
            for r in rows:
                md = r.get('measurement_date')
                wl = r.get('water_level_m')
                prev = r.get('prev_level')
                if md:
                    try:
                        y, mth, d = map(int, md.split('-'))
                        ord_val = datetime(y, mth, d).date().toordinal()
                        latest_dates.append(md)
                        if ord_val >= thirty_days_ago_ord:
                            uptodate += 1
                    except Exception:
                        pass
                if wl is not None and prev is not None:
                    try:
                        drop = prev - wl
                        if drop < -0.5:
                            declining += 1
                    except Exception:
                        pass
            latest_reading = max(latest_dates) if latest_dates else None
            uptodate_percent = round((uptodate / monitoring_count) * 100, 1)
            return {
                'monitoring_count': monitoring_count,
                'uptodate_percent': uptodate_percent,
                'declining_count': declining,
                'latest_reading': latest_reading
            }
        except Exception:
            # Fallback legacy path
            thirty_days_ago = datetime.now().date().toordinal() - 30
            msources = self.db.execute_query("SELECT source_id FROM water_sources WHERE source_purpose = 'MONITORING'")
            monitoring_ids = [r['source_id'] for r in msources]
            monitoring_count = len(monitoring_ids)
            if monitoring_count == 0:
                return {
                    'monitoring_count': 0,
                    'uptodate_percent': 0,
                    'declining_count': 0,
                    'latest_reading': None
                }
            latest_rows = self.db.execute_query(
                "SELECT source_id, MAX(measurement_date) AS max_date FROM measurements WHERE source_id IN (" + ",".join(str(i) for i in monitoring_ids) + ") GROUP BY source_id"
            )
            uptodate = 0
            all_dates = []
            for row in latest_rows:
                md = row['max_date']
                if md:
                    try:
                        y, mth, d = map(int, md.split('-'))
                        ordinal = datetime(y, mth, d).date().toordinal()
                        all_dates.append(md)
                        if ordinal >= thirty_days_ago:
                            uptodate += 1
                    except Exception:
                        continue
            uptodate_percent = round((uptodate / monitoring_count) * 100, 1)
            latest_reading = max(all_dates) if all_dates else None
            declining_count = 0
            for sid in monitoring_ids:
                two_rows = self.db.execute_query(
                    "SELECT water_level_m FROM measurements WHERE source_id = ? AND water_level_m IS NOT NULL ORDER BY measurement_date DESC LIMIT 2",
                    (sid,)
                )
                if len(two_rows) == 2:
                    try:
                        if two_rows[0]['water_level_m'] is not None and two_rows[1]['water_level_m'] is not None:
                            drop = two_rows[1]['water_level_m'] - two_rows[0]['water_level_m']
                            if drop < -0.5:
                                declining_count += 1
                    except Exception:
                        pass
            return {
                'monitoring_count': monitoring_count,
                'uptodate_percent': uptodate_percent,
                'declining_count': declining_count,
                'latest_reading': latest_reading
            }

    def _fetch_borehole_levels_table(self):
        """Fetch borehole level records for Data tab (limited)."""
        rows = self.db.execute_query(
            """
            SELECT ws.source_name, m.measurement_date, m.water_level_m, m.static_level_m
            FROM measurements m
            JOIN water_sources ws ON m.source_id = ws.source_id
            WHERE ws.source_purpose = 'MONITORING'
                  AND m.water_level_m IS NOT NULL
            ORDER BY m.measurement_date DESC
            LIMIT 200
            """
        )
        # Transform for display
        table_rows = []
        for r in rows:
            table_rows.append((
                r.get('source_name',''),
                r.get('measurement_date',''),
                f"{r.get('water_level_m'):.2f}" if r.get('water_level_m') is not None else '',
                f"{r.get('static_level_m'):.2f}" if r.get('static_level_m') is not None else ''
            ))
        return table_rows

    def _fetch_borehole_levels_latest_table(self):
        """Fetch latest reading per monitoring borehole."""
        rows = self.db.execute_query(
            """
            SELECT ws.source_name,
                   MAX(m.measurement_date) AS latest_date,
                   (SELECT water_level_m FROM measurements m2 WHERE m2.source_id = ws.source_id AND m2.measurement_date = MAX(m.measurement_date) LIMIT 1) AS latest_level,
                   (SELECT static_level_m FROM measurements m3 WHERE m3.source_id = ws.source_id AND m3.measurement_date = MAX(m.measurement_date) LIMIT 1) AS latest_static
            FROM water_sources ws
            LEFT JOIN measurements m ON ws.source_id = m.source_id AND m.water_level_m IS NOT NULL
            WHERE ws.source_purpose = 'MONITORING'
            GROUP BY ws.source_id, ws.source_name
            ORDER BY ws.source_name
            """
        )
        table_rows = []
        for r in rows:
            table_rows.append((
                r.get('source_name',''),
                r.get('latest_date','') or '—',
                f"{r.get('latest_level'):.2f}" if r.get('latest_level') is not None else '',
                f"{r.get('latest_static'):.2f}" if r.get('latest_static') is not None else ''
            ))
        return table_rows

    def _derive_date_bounds(self, range_label):
        """Return (date_from, date_to) ISO strings based on selected range label.
        Only derives start date; end date defaults to today. Custom not implemented yet (returns None bounds).
        """
        today = datetime.now().date()
        if range_label == 'Last 7d':
            start = today.replace()  # copy
            start_ordinal = today.toordinal() - 7
            start_dt = datetime.fromordinal(start_ordinal).date()
            return start_dt.isoformat(), today.isoformat()
        if range_label == 'Last 30d' or range_label == '':
            start_ordinal = today.toordinal() - 30
            start_dt = datetime.fromordinal(start_ordinal).date()
            return start_dt.isoformat(), today.isoformat()
        if range_label == 'YTD':
            start_dt = today.replace(month=1, day=1)
            return start_dt.isoformat(), today.isoformat()
        # Custom or unknown
        return None, None

    def _fetch_borehole_static_filtered_table(self):
        """Fetch static water level measurements applying site/date filters.
        Returns rows: (Borehole, Date, Static Level)
        """
        params = []
        where_clauses = ["ws.source_purpose = 'MONITORING'", "m.static_level_m IS NOT NULL", "m.measurement_type = 'static_level'"]
        if self.date_from:
            where_clauses.append("m.measurement_date >= ?")
            params.append(self.date_from)
        if self.date_to:
            where_clauses.append("m.measurement_date <= ?")
            params.append(self.date_to)
        if self.selected_sites:
            placeholders = ",".join(["?" for _ in self.selected_sites])
            # Match either source_code or source_name for robustness
            where_clauses.append(f"(ws.source_code IN ({placeholders}) OR ws.source_name IN ({placeholders}))")
            params.extend(self.selected_sites)
            params.extend(self.selected_sites)
        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT COALESCE(ws.source_code, ws.source_name) AS site_label, m.measurement_date, m.static_level_m
            FROM measurements m
            JOIN water_sources ws ON m.source_id = ws.source_id
            WHERE {where_sql}
            ORDER BY m.measurement_date DESC
            LIMIT 500
        """
        rows = self.db.execute_query(query, tuple(params))
        table_rows = []
        for r in rows:
            table_rows.append((
                r.get('site_label',''),
                r.get('measurement_date',''),
                f"{r.get('static_level_m'):.2f}" if r.get('static_level_m') is not None else ''
            ))
        return table_rows

    def _fetch_quality_category_rows(self):
        """Fetch rows for quality categories (groundwater, surface water, PCD, STP).
        Returns list of dicts: {'site_label': str, 'measurement_date': str, 'values': {friendly: value}}"""
        params = []
        where_clauses = ["ws.source_purpose = 'MONITORING'", "m.measurement_type IN ('quality_groundwater','quality_surface')"]
        # Category-specific source code filtering
        if self.active_category == 'groundwater_quality':
            where_clauses.append("m.measurement_type = 'quality_groundwater'")
        elif self.active_category == 'surface_water':
            where_clauses.append("m.measurement_type = 'quality_surface'")
            where_clauses.append("(ws.source_code NOT LIKE 'PCD%' AND ws.source_code NOT LIKE 'STP%')")
        elif self.active_category == 'pcd':
            where_clauses.append("m.measurement_type = 'quality_surface'")
            where_clauses.append("ws.source_code LIKE 'PCD%'")
        elif self.active_category == 'stp_effluent':
            where_clauses.append("m.measurement_type = 'quality_surface'")
            where_clauses.append("ws.source_code LIKE 'STP%'")
        if self.date_from:
            where_clauses.append("m.measurement_date >= ?")
            params.append(self.date_from)
        if self.date_to:
            where_clauses.append("m.measurement_date <= ?")
            params.append(self.date_to)
        if self.selected_sites:
            placeholders = ",".join(["?" for _ in self.selected_sites])
            where_clauses.append(f"(ws.source_code IN ({placeholders}) OR ws.source_name IN ({placeholders}))")
            params.extend(self.selected_sites)
            params.extend(self.selected_sites)
        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT ws.source_code, ws.source_name, m.measurement_date,
                   m.ph, m.conductivity, m.tds, m.static_level_m, m.temperature, m.turbidity, m.quality_notes
            FROM measurements m
            JOIN water_sources ws ON m.source_id = ws.source_id
            WHERE {where_sql}
            ORDER BY m.measurement_date DESC
            LIMIT 500
        """
        rows = self.db.execute_query(query, tuple(params))
        results = []
        for r in rows:
            site_label = r.get('source_name') or r.get('source_code') or ''
            date = r.get('measurement_date','')
            # Build value map using friendly names from templates logic
            value_map = {}
            # Direct fields
            direct_pairs = {
                'Static Level': r.get('static_level_m'),
                'Ph': r.get('ph'),
                'Conductivity': r.get('conductivity'),
                'Tds': r.get('tds'),
                'Temperature': r.get('temperature'),
                'Turbidity': r.get('turbidity')
            }
            for k,v in direct_pairs.items():
                if v is not None:
                    try:
                        value_map[k] = f"{float(v):.2f}" if isinstance(v,(int,float)) else str(v)
                    except Exception:
                        value_map[k] = str(v)
            # Quality notes JSON (ion / parameter set)
            qn = r.get('quality_notes')
            parsed = {}
            if qn:
                try:
                    import json as _json
                    parsed = _json.loads(qn)
                except Exception:
                    parsed = {}
            for key,val in parsed.items():
                # Friendly transform similar to _get_category_parameters
                friendly = key
                for suf in ['_mgL','_uScm','_m','_c','_ntu']:
                    if friendly.endswith(suf):
                        friendly = friendly.replace(suf,'')
                friendly = friendly.replace('_',' ').title()
                if friendly not in value_map:
                    try:
                        value_map[friendly] = f"{float(val):.2f}" if isinstance(val,(int,float)) else str(val)
                    except Exception:
                        value_map[friendly] = str(val)
            results.append({'site_label': site_label, 'measurement_date': date, 'values': value_map})
        return results

    def _reset_borehole_static_data(self):
        """Remove all static_level measurements for monitoring boreholes and seed fresh sample data."""
        if not messagebox.askyesno("Confirm Reset", "Delete ALL static level measurements for monitoring boreholes and seed sample rows? This cannot be undone."):
            return
        try:
            del_sql = "DELETE FROM measurements WHERE measurement_type = 'static_level' AND source_id IN (SELECT source_id FROM water_sources WHERE source_purpose = 'MONITORING')"
            deleted = self.db.execute_update(del_sql)
            sources = self.db.execute_query("SELECT source_id, source_code FROM water_sources WHERE source_purpose = 'MONITORING' ORDER BY source_code")
            today = datetime.now().date().isoformat()
            base = 15.0
            for idx, s in enumerate(sources):
                val = round(base - idx * 0.25, 2)
                data = {
                    'measurement_date': today,
                    'measurement_type': 'static_level',
                    'source_id': s['source_id'],
                    'facility_id': None,
                    'static_level_m': val,
                    'measured': 1,
                    'data_source': 'seed',
                    'notes': 'reset seed'
                }
                self.db.add_measurement(data)
            messagebox.showinfo("Reset Complete", f"Deleted {deleted} rows. Seeded {len(sources)} static level measurements.")
        except Exception as e:
            messagebox.showerror("Reset Failed", str(e))
        self._load_category_sites()
        self._render_active_view()

