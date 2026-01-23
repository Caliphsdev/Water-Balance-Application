"""UI tests for Monitoring Dashboard (tabs, filters, KPIs).

These tests instantiate the dashboard in a lightweight Tk context and stub
database interactions to avoid relying on real data. Focus areas:
- Sub-tab rendering and switching
- Category site list loading via DB
- KPI computation (declining logic) for borehole levels
- Date range derivation utility
"""

import tkinter as tk
import pytest


class FakeDb:
    """Minimal database stub for MonitoringDashboard tests.

    Provides only the methods used by the dashboard and returns predictable
    results based on the SQL content to simulate various views.
    """

    def register_listener(self, cb):
        self._listener = cb

    def execute_query(self, sql, params=None):
        sql = (sql or "").lower()
        # Count static level rows
        if "select count(*) as cnt from measurements where measurement_type = 'static_level'" in sql:
            return [{"cnt": 2}]
        # Category site lists
        if "measurement_type = 'static_level'" in sql:
            return [
                {"source_name": "BH-001"},
                {"source_name": "BH-002"},
            ]
        if "quality_surface" in sql and "pcd%" not in sql and "stp%" not in sql:
            return [{"source_name": "SW-Station-01"}]
        if "quality_surface" in sql and "pcd%" in sql:
            return [{"source_name": "PCD-01"}]
        if "quality_surface" in sql and "stp%" in sql:
            return [{"source_name": "STP-01"}]
        # KPI window function query (ranked rows)
        if "row_number() over" in sql:
            # Simulate two monitoring boreholes with latest and previous levels
            # BH-001: water level dropped (prev=11.0 → latest=10.0) should flag as declining
            # BH-002: water level rose (prev=11.0 → latest=12.0) should NOT flag
            return [
                {
                    "source_id": 1,
                    "source_name": "BH-001",
                    "measurement_date": "2026-01-15",
                    "water_level_m": 10.0,  # Latest reading (lower)
                    "prev_level": 11.0,      # Previous reading (higher) → DECLINING
                    "rn": 1,
                },
                {
                    "source_id": 2,
                    "source_name": "BH-002",
                    "measurement_date": "2026-01-15",
                    "water_level_m": 12.0,  # Latest reading (higher)
                    "prev_level": 11.0,      # Previous reading (lower) → RISING
                    "rn": 1,
                },
            ]
        # Quality rows used for Data tab (return empty for simplicity)
        if "select ws.source_code, ws.source_name" in sql and "from measurements" in sql:
            return []
        # Static filtered table (Data tab)
        if "m.static_level_m is not null" in sql and "order by m.measurement_date desc" in sql:
            return [
                {"site_label": "BH-001", "measurement_date": "2026-01-10", "static_level_m": 10.0},
                {"site_label": "BH-002", "measurement_date": "2026-01-09", "static_level_m": 11.2},
            ]
        return []

    def execute_update(self, sql, params=None):
        return 0

    def add_measurement(self, data):
        return 1


@pytest.fixture()
def tk_root():
    """Create a Tk root for UI tests and ensure cleanup."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def _build_dashboard_with_fake_db(tk_root):
    """Helper to create dashboard wired to a FakeDb."""
    from src.ui.monitoring_dashboard import MonitoringDashboard

    # Container frame to host the dashboard UI
    container = tk.Frame(tk_root)
    container.pack()

    dash = MonitoringDashboard(container)
    # Inject fake DB to avoid real queries
    dash.db = FakeDb()
    dash.load()
    return dash


def test_subtabs_present_and_switching(tk_root):
    """Verify sub-tab bar renders and switching updates the active view."""
    dash = _build_dashboard_with_fake_db(tk_root)

    # Subtab labels should be present
    bar_children = dash.subtab_bar.winfo_children()
    labels = [w.cget("text") for w in bar_children if isinstance(w, tk.Button)]
    assert labels[:3] == ["Stats", "Charts", "Data"]

    # Switch to Data tab and ensure state updates
    dash._switch_subtab("data")
    assert dash.active_subtab == "data"
    assert "data" in dash._tab_frames


def test_category_site_list_loads(tk_root):
    """List of sites populates for current category using DB stub."""
    dash = _build_dashboard_with_fake_db(tk_root)
    # Borehole levels selected by default
    sites = [dash.site_listbox.get(i) for i in range(dash.site_listbox.size())]
    assert sites == ["BH-001", "BH-002"]

    # Switch category to PCD and rebuild sites
    dash._switch_category("pcd")
    pcd_sites = [dash.site_listbox.get(i) for i in range(dash.site_listbox.size())]
    # Fake DB returns one PCD site
    assert pcd_sites == ["PCD-01"]


def test_borehole_kpis_decline_logic_flags_decline(tk_root):
    """Declining logic should flag BH-001 (water level dropped: prev > latest by >0.5m)."""
    dash = _build_dashboard_with_fake_db(tk_root)
    stats = dash._compute_borehole_level_kpis()
    assert stats["monitoring_count"] == 2
    # Expect exactly one declining borehole (BH-001: 11.0 → 10.0 = 1.0m drop)
    assert stats["declining_count"] == 1


def test_derive_date_bounds_basic():
    """Date range derivation returns reasonable ISO bounds for presets."""
    from src.ui.monitoring_dashboard import MonitoringDashboard

    # Use a dummy frame for construction
    root = tk.Tk(); root.withdraw()
    try:
        dash = MonitoringDashboard(root)
        start7, end7 = dash._derive_date_bounds("Last 7d")
        assert isinstance(start7, str) and isinstance(end7, str)

        start30, end30 = dash._derive_date_bounds("Last 30d")
        assert isinstance(start30, str) and isinstance(end30, str)

        start_ytd, end_ytd = dash._derive_date_bounds("YTD")
        # YTD start should be January 1st
        assert start_ytd.endswith("-01-01")
        assert isinstance(end_ytd, str)
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def test_category_switch_preserves_content_area(tk_root):
    """Switching categories should not destroy the content area frame."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Capture original content area reference
    original_content_area = dash._content_area
    
    # Switch to a different category
    dash._switch_category("surface_water")
    
    # Content area should still exist and be the same object
    assert hasattr(dash, '_content_area')
    assert dash._content_area.winfo_exists()
    assert dash._content_area is original_content_area


def test_filter_application_refreshes_view(tk_root):
    """Applying filters should update internal state and refresh the current view."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Select a site in the listbox
    dash.site_listbox.selection_set(0)
    
    # Apply filters
    dash._apply_filters()
    
    # Should have selected site stored
    assert len(dash.selected_sites) == 1
    assert dash.selected_sites[0] == "BH-001"


def test_empty_data_renders_without_crash(tk_root):
    """Dashboard should render gracefully when DB returns no data."""
    from src.ui.monitoring_dashboard import MonitoringDashboard
    
    class EmptyDb:
        def register_listener(self, cb):
            pass
        def execute_query(self, sql, params=None):
            return []
        def execute_update(self, sql, params=None):
            return 0
    
    container = tk.Frame(tk_root)
    container.pack()
    dash = MonitoringDashboard(container)
    dash.db = EmptyDb()
    
    # Should not crash even with empty DB
    dash.load()
    assert dash.active_category == "borehole_levels"
    assert dash.active_subtab == "stats"


def test_custom_date_range_picker_shows_on_select(tk_root):
    """Custom date picker should appear when 'Custom' is selected in date range."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Initially, date picker should be hidden
    assert dash.date_picker_frame is not None
    assert dash.date_picker_frame.winfo_manager() == ''  # Not packed
    
    # Select "Custom" from dropdown
    dash.date_range_cb.current(3)  # Custom is index 3
    dash._on_date_range_changed()
    
    # Date picker should now be visible
    assert dash.date_picker_frame.winfo_manager() != ''  # Packed


def test_filter_panel_collapse_expand(tk_root):
    """Filter panel should collapse/expand on button click."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Initially collapsed (to maximize chart space)
    assert dash.filter_collapsed
    assert dash.filter_content_frame.winfo_manager() == ''
    
    # Toggle expand
    dash._toggle_filter_panel()
    assert not dash.filter_collapsed
    assert dash.filter_content_frame.winfo_manager() != ''
    
    # Toggle collapse again
    dash._toggle_filter_panel()
    assert dash.filter_collapsed
    assert dash.filter_content_frame.winfo_manager() == ''


def test_chart_options_collapse_expand(tk_root):
    """Chart options section should collapse/expand in Data tab."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Switch to Data tab
    dash._switch_subtab("data")
    
    # Initially expanded
    assert not dash.chart_options_collapsed
    assert dash.chart_options_frame.winfo_manager() != ''
    
    # Toggle collapse
    dash._toggle_chart_options()
    assert dash.chart_options_collapsed
    assert dash.chart_options_frame.winfo_manager() == ''
    
    # Toggle expand
    dash._toggle_chart_options()
    assert not dash.chart_options_collapsed
    assert dash.chart_options_frame.winfo_manager() != ''


def test_custom_date_range_applied_in_filters(tk_root):
    """Custom date range from entry fields should be applied."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Select "Custom" and enter dates
    dash.date_range_cb.current(3)  # Custom
    dash._on_date_range_changed()
    
    # Clear default placeholder and enter dates
    dash.date_from_entry.delete(0, 'end')
    dash.date_from_entry.insert(0, "2026-01-01")
    dash.date_to_entry.delete(0, 'end')
    dash.date_to_entry.insert(0, "2026-01-31")
    
    # Apply filters
    dash._apply_filters()
    
    # Custom dates should be set
    assert dash.date_from == "2026-01-01"
    assert dash.date_to == "2026-01-31"


# ==================== Integration Tests ====================
# These tests verify actual UI rendering and widget state

def test_filter_panel_widgets_exist(tk_root):
    """Verify all filter panel widgets render and are accessible."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Check filter panel exists
    assert dash.filter_panel is not None
    assert dash.filter_panel.winfo_exists()
    
    # Check collapse button exists
    assert hasattr(dash, 'filter_collapse_btn')
    assert dash.filter_collapse_btn.winfo_exists()
    
    # Check date range combobox exists
    assert dash.date_range_cb is not None
    assert dash.date_range_cb.winfo_exists()
    assert dash.date_range_cb.get() == "Last 30d"  # Default
    
    # Check date picker frame exists (but hidden initially)
    assert dash.date_picker_frame is not None
    assert dash.date_picker_frame.winfo_exists()
    assert dash.date_picker_frame.winfo_manager() == ''  # Not packed
    
    # Check date entry fields exist
    assert dash.date_from_entry is not None
    assert dash.date_to_entry is not None
    assert dash.date_from_entry.winfo_exists()
    assert dash.date_to_entry.winfo_exists()
    
    # Check site listbox exists
    assert dash.site_listbox is not None
    assert dash.site_listbox.winfo_exists()
    assert dash.site_listbox.size() > 0  # Has sites loaded


def test_date_picker_visibility_toggle(tk_root):
    """Verify date picker shows/hides based on date range selection."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Test preset date ranges hide the picker
    for idx, preset in enumerate(["Last 7d", "Last 30d", "YTD"]):
        dash.date_range_cb.current(idx)
        dash._on_date_range_changed()
        assert dash.date_picker_frame.winfo_manager() == '', f"Picker should be hidden for {preset}"
    
    # Test "Custom" shows the picker
    dash.date_range_cb.current(3)  # Custom
    dash._on_date_range_changed()
    assert dash.date_picker_frame.winfo_manager() != '', "Picker should be visible for Custom"


def test_filter_content_frame_visibility(tk_root):
    """Verify filter content frame shows/hides when collapsed."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Initially should be hidden (collapsed by default to maximize chart space)
    assert dash.filter_content_frame.winfo_exists()
    assert dash.filter_content_frame.winfo_manager() == ''
    assert dash.filter_collapsed is True
    
    # Expand it
    dash._toggle_filter_panel()
    assert dash.filter_content_frame.winfo_manager() != ''
    assert dash.filter_collapsed is False
    
    # Collapse it again
    dash._toggle_filter_panel()
    assert dash.filter_content_frame.winfo_manager() == ''
    assert dash.filter_collapsed is True


def test_chart_options_widget_exists_in_data_tab(tk_root):
    """Verify chart options section renders in Data tab."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Switch to Data tab
    dash._switch_subtab("data")
    
    # Check chart options button and frame exist
    assert hasattr(dash, 'chart_options_collapse_btn')
    assert dash.chart_options_collapse_btn.winfo_exists()
    
    assert dash.chart_options_frame is not None
    assert dash.chart_options_frame.winfo_exists()
    
    # Should be visible initially
    assert dash.chart_options_frame.winfo_manager() != ''
    assert not dash.chart_options_collapsed


def test_chart_options_collapse_visibility(tk_root):
    """Verify chart options frame hides when collapsed."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Switch to Data tab to render chart options
    dash._switch_subtab("data")
    
    # Initially visible
    initial_state = dash.chart_options_frame.winfo_manager()
    assert initial_state != ''
    
    # Collapse
    dash._toggle_chart_options()
    assert dash.chart_options_collapsed is True
    assert dash.chart_options_frame.winfo_manager() == ''
    
    # Expand
    dash._toggle_chart_options()
    assert dash.chart_options_collapsed is False
    assert dash.chart_options_frame.winfo_manager() != ''


def test_data_table_renders_with_columns(tk_root):
    """Verify data table renders in Data tab without errors."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Switch to Data tab
    dash._switch_subtab("data")
    
    # Get the data frame
    data_frame = dash._tab_frames.get('data')
    assert data_frame is not None
    assert data_frame.winfo_exists()
    
    # Data table should render without crashing (frame exists)
    # The treeview is nested inside the table_frame which is inside data_frame
    assert len(data_frame.winfo_children()) > 0, "Data tab should have child widgets"


def test_category_switch_updates_sites_in_filter(tk_root):
    """Verify switching categories updates sites list in filter panel."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Initially borehole_levels
    sites_bh = [dash.site_listbox.get(i) for i in range(dash.site_listbox.size())]
    assert "BH-001" in sites_bh
    
    # Switch to PCD category
    dash._switch_category("pcd")
    
    # Sites list should update
    sites_pcd = [dash.site_listbox.get(i) for i in range(dash.site_listbox.size())]
    assert "PCD-01" in sites_pcd
    assert "BH-001" not in sites_pcd


def test_apply_filters_updates_table_display(tk_root):
    """Verify applying filters refreshes the data table."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Switch to Data tab
    dash._switch_subtab("data")
    
    # Select a site
    dash.site_listbox.selection_set(0)
    
    # Apply filters
    dash._apply_filters()
    
    # Verify filter state was updated
    assert len(dash.selected_sites) == 1
    
    # Data table should still render without error
    data_frame = dash._tab_frames.get('data')
    assert data_frame.winfo_exists()


def test_filter_panel_collapse_button_text_changes(tk_root):
    """Verify collapse button shows correct icon when toggled."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Initially collapsed (▶)
    initial_text = dash.filter_collapse_btn.cget("text")
    assert "▶" in initial_text
    
    # Expand
    dash._toggle_filter_panel()
    expanded_text = dash.filter_collapse_btn.cget("text")
    assert "▼" in expanded_text
    
    # Collapse again
    dash._toggle_filter_panel()
    collapsed_text = dash.filter_collapse_btn.cget("text")
    assert "▶" in collapsed_text


def test_chart_options_button_text_changes(tk_root):
    """Verify chart options button shows correct icon when toggled."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Switch to Data tab
    dash._switch_subtab("data")
    
    # Initially expanded (▼)
    initial_text = dash.chart_options_collapse_btn.cget("text")
    assert "▼" in initial_text
    
    # Collapse
    dash._toggle_chart_options()
    collapsed_text = dash.chart_options_collapse_btn.cget("text")
    assert "▶" in collapsed_text
    
    # Expand
    dash._toggle_chart_options()
    expanded_text = dash.chart_options_collapse_btn.cget("text")
    assert "▼" in expanded_text


def test_date_entry_fields_have_default_placeholders(tk_root):
    """Verify date entry fields have YYYY-MM-DD placeholder text."""
    dash = _build_dashboard_with_fake_db(tk_root)
    
    # Check default placeholder text
    from_text = dash.date_from_entry.get()
    to_text = dash.date_to_entry.get()
    
    assert "YYYY-MM-DD" in from_text or from_text == ""
    assert "YYYY-MM-DD" in to_text or to_text == ""
