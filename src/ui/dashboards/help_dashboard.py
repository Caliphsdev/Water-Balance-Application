"""
Help Dashboard Controller (DOCUMENTATION & SUPPORT).

Purpose:
- Load help.ui (container for help content)
- Populate a practical in-app help library from actual code behavior
"""

from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ui.dashboards.generated_ui_help import Ui_Form

try:
    from services.calculation.balance_service import EXCEL_COLUMNS
except Exception:  # pragma: no cover - safe fallback if imports are unavailable during tooling
    EXCEL_COLUMNS = {}

HELP_BASE_CSS = """
<style>
body {
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    line-height: 1.55;
    color: #0f172a;
}
h2 {
    font-size: 33px;
    margin: 4px 0 10px 0;
    color: #0b2346;
}
h3 {
    font-size: 17px;
    margin: 16px 0 8px 0;
    color: #0f274d;
}
ul, ol { margin-top: 4px; margin-bottom: 8px; }
li { margin: 2px 0; }
code {
    background: #eef3f8;
    border: 1px solid #d5dee8;
    border-radius: 4px;
    padding: 1px 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}
.formula-block {
    background: #f8fafc;
    border: 1px solid #d7e0ea;
    border-left: 4px solid #1d4ed8;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 8px 0;
    white-space: pre-wrap;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    line-height: 1.5;
}
.source-ref {
    margin-top: 6px;
    color: #52627a;
    font-size: 12px;
    line-height: 1.45;
    overflow-wrap: anywhere;
    word-break: break-word;
}
.source-ref code {
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
}
.formula-note {
    margin: 6px 0 8px 0;
    color: #243b5c;
}
.human-def {
    background: #fbfdff;
    border: 1px solid #d7e2ef;
    border-radius: 8px;
    padding: 8px 10px;
    margin: 6px 0 10px 0;
}
.formula-card {
    background: #f8fbff;
    border: 1px solid #d5e0ee;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0 12px 0;
}
.eqn {
    display: block;
    font-family: "Cambria Math", "Times New Roman", serif;
    font-size: 18px;
    color: #102a4b;
    margin: 4px 0;
}
.term-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    font-size: 12px;
}
.term-table th, .term-table td {
    border: 1px solid #d5e0ee;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
}
.term-table th {
    background: #eef4fb;
    color: #17345a;
}
</style>
"""


class HelpPage(QWidget):
    """Help Page (DOCUMENTATION LIBRARY)."""

    def __init__(self, parent=None):
        """Initialize Help page."""
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._tab_browsers: dict[QWidget, QTextBrowser] = {}
        self._tab_toc_lists: dict[QWidget, QListWidget] = {}
        self._index_entries: list[dict[str, object]] = []
        self._tab_sections: dict[int, list[dict[str, str]]] = {}
        self._filtered_entries: list[dict[str, object]] = []
        self._is_applying_filter = False
        self._populate_help_library()
        self._build_help_toolbar()
        self._build_index_entries()
        self._build_tab_sections()
        self._apply_index_filter("")
        self.ui.help_tab.currentChanged.connect(self._refresh_on_this_page)
        self._refresh_on_this_page(self.ui.help_tab.currentIndex())

    def _populate_help_library(self) -> None:
        """Replace placeholder labels with rich, code-derived help content."""
        for attr in ("label_4", "label_5", "label_6", "label_7", "label_8", "label_9", "label_10", "label_11"):
            lbl = getattr(self.ui, attr, None)
            if isinstance(lbl, QLabel):
                lbl.hide()

        self.ui.help_tab.setCurrentIndex(0)

        self._set_tab_content(self.ui.Overview, self._build_overview_html())
        self._set_tab_content(self.ui.Dashboards, self._build_dashboards_html())
        self._set_tab_content(self.ui.Calculations, self._build_calculations_html())
        self._set_tab_content(self.ui.Formulas, self._build_formulas_html())
        self._set_tab_content(self.ui.WaterSources, self._build_water_sources_html())
        self._set_tab_content(self.ui.Storage, self._build_storage_html())
        self._set_tab_content(self.ui.Features, self._build_features_html())
        self._set_tab_content(self.ui.Troubleshooting, self._build_troubleshooting_html())

    def _build_help_toolbar(self) -> None:
        """Create quick-index and search controls above the tab widget."""
        toolbar = QWidget(self)
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(8)

        row.addWidget(QLabel("Index:", toolbar))
        self._index_combo = QComboBox(toolbar)
        self._index_combo.setMinimumWidth(280)
        row.addWidget(self._index_combo)

        row.addWidget(QLabel("Filter topics:", toolbar))
        self._index_filter_edit = QLineEdit(toolbar)
        self._index_filter_edit.setPlaceholderText("e.g. storage, runoff, recycled, troubleshooting")
        self._index_filter_edit.setMinimumWidth(280)
        row.addWidget(self._index_filter_edit)

        row.addWidget(QLabel("Find in tab:", toolbar))
        self._search_edit = QLineEdit(toolbar)
        self._search_edit.setPlaceholderText("Search current section text")
        self._search_edit.setMinimumWidth(220)
        row.addWidget(self._search_edit)

        self._find_prev_btn = QPushButton("Prev", toolbar)
        self._find_next_btn = QPushButton("Next", toolbar)
        self._clear_search_btn = QPushButton("Clear", toolbar)
        self._find_prev_btn.setIcon(QIcon(":/icons/previous_icon.svg"))
        self._find_next_btn.setIcon(QIcon(":/icons/next_icon.svg"))
        self._clear_search_btn.setIcon(QIcon(":/icons/clear.svg"))
        self._find_prev_btn.setIconSize(QSize(14, 14))
        self._find_next_btn.setIconSize(QSize(14, 14))
        self._clear_search_btn.setIconSize(QSize(14, 14))
        self._find_prev_btn.setMinimumHeight(30)
        self._find_next_btn.setMinimumHeight(30)
        self._clear_search_btn.setMinimumHeight(30)
        self._find_prev_btn.setMaximumHeight(30)
        self._find_next_btn.setMaximumHeight(30)
        self._clear_search_btn.setMaximumHeight(30)
        row.addWidget(self._find_prev_btn)
        row.addWidget(self._find_next_btn)
        row.addWidget(self._clear_search_btn)

        self._search_status = QLabel("", toolbar)
        self._search_status.setObjectName("helpSearchStatus")
        self._search_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        row.addWidget(self._search_status)
        row.addStretch(1)

        self.ui.gridLayout.removeWidget(self.ui.help_tab)
        self.ui.gridLayout.addWidget(toolbar, 1, 0, 1, 1)
        self.ui.gridLayout.addWidget(self.ui.help_tab, 2, 0, 1, 1)

        self._index_combo.currentIndexChanged.connect(self._open_selected_index_entry)
        self._index_filter_edit.textChanged.connect(self._apply_index_filter)
        self._find_next_btn.clicked.connect(self._find_next)
        self._find_prev_btn.clicked.connect(self._find_prev)
        self._clear_search_btn.clicked.connect(self._clear_search)
        self._search_edit.returnPressed.connect(self._find_next)

    def _build_index_entries(self) -> None:
        """Prepare quick-link index entries."""
        self._index_entries = [
            {"label": "Overview - System", "tab": 0, "anchor": "overview-system", "kw": "overview system architecture workflow"},
            {"label": "Overview - Data Stores", "tab": 0, "anchor": "overview-data-stores", "kw": "database excel json storage history"},
            {"label": "Dashboards - Analytics", "tab": 1, "anchor": "dash-analytics", "kw": "analytics chart meter readings"},
            {"label": "Dashboards - Monitoring", "tab": 1, "anchor": "dash-monitoring", "kw": "monitoring borehole pcd static"},
            {"label": "Dashboards - Flow Diagram", "tab": 1, "anchor": "dash-flow", "kw": "flow diagram recirculation categorize"},
            {"label": "Calculations - Engine Order", "tab": 2, "anchor": "calc-order", "kw": "calculate order service inflow outflow"},
            {"label": "Calculations - Data Quality", "tab": 2, "anchor": "calc-quality", "kw": "quality missing estimated warning"},
            {"label": "Formulas - Master Equation", "tab": 3, "anchor": "formula-master", "kw": "error percent closure equation"},
            {"label": "Formulas - Inflows", "tab": 3, "anchor": "formula-inflows", "kw": "rainfall runoff ore moisture abstraction"},
            {"label": "Formulas - Outflows", "tab": 3, "anchor": "formula-outflows", "kw": "evaporation seepage dust tailings"},
            {"label": "Water Sources - Excel Columns", "tab": 4, "anchor": "sources-excel", "kw": "excel columns meter readings rwd"},
            {"label": "Storage - Opening/Closing", "tab": 5, "anchor": "storage-opening-closing", "kw": "opening closing delta history"},
            {"label": "Features - Performance", "tab": 6, "anchor": "features-performance", "kw": "thread background cache export"},
            {"label": "Troubleshooting - Checklist", "tab": 7, "anchor": "trouble-checklist", "kw": "checklist run fail missing"},
        ]

    def _apply_index_filter(self, text: str) -> None:
        """Filter quick-link index by label and keywords."""
        query = (text or "").strip().lower()
        self._filtered_entries = []
        self._is_applying_filter = True
        try:
            self._index_combo.clear()
            for entry in self._index_entries:
                hay = f"{entry['label']} {entry['kw']}".lower()
                if not query or query in hay:
                    self._filtered_entries.append(entry)
                    self._index_combo.addItem(str(entry["label"]))
            if self._index_combo.count() == 0:
                self._index_combo.addItem("No matching topics")
        finally:
            self._is_applying_filter = False

    def _open_selected_index_entry(self, index: int) -> None:
        """Jump to tab and anchor from selected quick-link entry."""
        if self._is_applying_filter:
            return
        if index < 0 or index >= len(self._filtered_entries):
            return
        entry = self._filtered_entries[index]
        tab_index = int(entry["tab"])
        anchor = str(entry["anchor"])
        self.ui.help_tab.setCurrentIndex(tab_index)
        tab_widget = self.ui.help_tab.widget(tab_index)
        browser = self._tab_browsers.get(tab_widget)
        if browser is not None:
            browser.scrollToAnchor(anchor)

    def _current_browser(self) -> QTextBrowser | None:
        tab = self.ui.help_tab.currentWidget()
        return self._tab_browsers.get(tab)

    def _find_next(self) -> None:
        self._find_in_current(forward=True)

    def _find_prev(self) -> None:
        self._find_in_current(forward=False)

    def _find_in_current(self, forward: bool) -> None:
        """Find text in current tab and wrap when needed."""
        browser = self._current_browser()
        text = self._search_edit.text().strip()
        if browser is None or not text:
            self._search_status.setText("")
            return

        flags = QTextDocument.FindFlags()
        if not forward:
            flags |= QTextDocument.FindBackward

        found = browser.find(text, flags)
        if not found:
            cursor = browser.textCursor()
            cursor.movePosition(QTextCursor.Start if forward else QTextCursor.End)
            browser.setTextCursor(cursor)
            found = browser.find(text, flags)

        self._search_status.setText("Match found" if found else "No match")

    def _clear_search(self) -> None:
        self._search_edit.clear()
        self._search_status.setText("")
        browser = self._current_browser()
        if browser is None:
            return
        cursor = browser.textCursor()
        cursor.clearSelection()
        browser.setTextCursor(cursor)

    def _set_tab_content(self, tab: QWidget, html: str) -> None:
        """Attach content browser + right-side section list to a tab."""
        layout = tab.layout()
        if layout is None:
            layout = QHBoxLayout(tab)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

        content_wrap = QFrame(tab)
        content_layout = QVBoxLayout(content_wrap)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        browser = QTextBrowser(tab)
        browser.setOpenExternalLinks(False)
        browser.setReadOnly(True)
        browser.setHtml(self._wrap_help_html(html))
        content_layout.addWidget(browser)
        layout.addWidget(content_wrap, 5)

        toc_wrap = QFrame(tab)
        toc_wrap.setObjectName("helpTocFrame")
        toc_wrap.setMinimumWidth(230)
        toc_wrap.setMaximumWidth(260)
        toc_layout = QVBoxLayout(toc_wrap)
        toc_layout.setContentsMargins(8, 8, 8, 8)
        toc_layout.setSpacing(6)
        toc_title = QLabel("On this page", toc_wrap)
        toc_title.setObjectName("helpTocTitle")
        toc_layout.addWidget(toc_title)
        toc_list = QListWidget(toc_wrap)
        toc_list.setObjectName("helpTocList")
        toc_list.setCursor(Qt.PointingHandCursor)
        toc_list.setStyleSheet(
            """
            QListWidget#helpTocList {
                border: 1px solid #c9d4e3;
                border-radius: 8px;
                background: #f8fbff;
                padding: 4px;
            }
            QListWidget#helpTocList::item {
                border-radius: 6px;
                padding: 6px 8px;
                color: #17345a;
            }
            QListWidget#helpTocList::item:hover {
                background: #e7f0ff;
                color: #0f2f57;
            }
            QListWidget#helpTocList::item:selected {
                background: #d9e8ff;
                color: #0b2f5f;
                font-weight: 600;
            }
            """
        )
        toc_list.itemClicked.connect(self._open_toc_entry)
        toc_layout.addWidget(toc_list, 1)
        layout.addWidget(toc_wrap, 1)

        self._tab_browsers[tab] = browser
        self._tab_toc_lists[tab] = toc_list

    def _build_tab_sections(self) -> None:
        """Build per-tab section metadata for right-side navigator."""
        self._tab_sections = {
            0: [
                {"title": "System overview", "anchor": "overview-system"},
                {"title": "Main pages", "anchor": "overview-main-pages"},
                {"title": "Primary data stores", "anchor": "overview-data-stores"},
            ],
            1: [
                {"title": "Analytics", "anchor": "dash-analytics"},
                {"title": "Monitoring", "anchor": "dash-monitoring"},
                {"title": "Storage facilities", "anchor": "dash-storage"},
                {"title": "Calculations", "anchor": "dash-calculations"},
                {"title": "Flow diagram", "anchor": "dash-flow"},
                {"title": "Settings", "anchor": "dash-settings"},
            ],
            2: [
                {"title": "Engine order", "anchor": "calc-order"},
                {"title": "System balance tab", "anchor": "calc-system-tab"},
                {"title": "Recycled tab", "anchor": "calc-recycled-tab"},
                {"title": "Data quality tab", "anchor": "calc-quality"},
                {"title": "Days of operation", "anchor": "calc-days-tab"},
            ],
            3: [
                {"title": "Master equation", "anchor": "formula-master"},
                {"title": "Inflows", "anchor": "formula-inflows"},
                {"title": "Outflows", "anchor": "formula-outflows"},
                {"title": "Storage", "anchor": "formula-storage"},
                {"title": "Flow closure", "anchor": "formula-flow"},
                {"title": "Worked example", "anchor": "formula-worked"},
            ],
            4: [
                {"title": "Environmental source", "anchor": "sources-env"},
                {"title": "Storage source", "anchor": "sources-storage-db"},
                {"title": "Excel columns", "anchor": "sources-excel"},
                {"title": "Surface abstraction", "anchor": "sources-surface"},
                {"title": "Groundwater abstraction", "anchor": "sources-ground"},
                {"title": "Dewatering", "anchor": "sources-dewater"},
            ],
            5: [
                {"title": "Opening and closing", "anchor": "storage-opening-closing"},
                {"title": "Persistence", "anchor": "storage-persistence"},
                {"title": "Warnings", "anchor": "storage-warnings"},
            ],
            6: [
                {"title": "Platform features", "anchor": "features-performance"},
            ],
            7: [
                {"title": "Common issues", "anchor": "trouble-common"},
                {"title": "Pre-run checklist", "anchor": "trouble-checklist"},
                {"title": "Closure targets", "anchor": "trouble-targets"},
            ],
        }

    def _refresh_on_this_page(self, tab_index: int) -> None:
        """Populate right-side section list for current tab."""
        tab = self.ui.help_tab.widget(tab_index)
        toc = self._tab_toc_lists.get(tab)
        if toc is None:
            return
        toc.clear()
        for section in self._tab_sections.get(tab_index, []):
            item = QListWidgetItem(section["title"])
            item.setData(Qt.UserRole, section["anchor"])
            toc.addItem(item)

    def _open_toc_entry(self, item: QListWidgetItem) -> None:
        """Scroll the current tab to selected anchor."""
        anchor = str(item.data(Qt.UserRole) or "")
        browser = self._current_browser()
        if browser and anchor:
            browser.scrollToAnchor(anchor)

    @staticmethod
    def _wrap_help_html(content: str) -> str:
        return HELP_BASE_CSS + content

    def _build_overview_html(self) -> str:
        return """
        <a name="overview-system"></a>
        <h2>System Overview</h2>
        <p>
            This application supports monthly mine-water accounting for operations, technical review, and management sign-off.
            It combines production, abstraction, environmental conditions, and storage behavior into one balanced monthly view.
        </p>
        <h3>How the system runs (high level)</h3>
        <ol>
            <li>Load approved source data (meter workbook, climate records, storage register).</li>
            <li>Calculate inflows, outflows, storage movement, recycled water, and KPI summaries.</li>
            <li>Assess closure quality and data reliability flags for the selected month.</li>
            <li>Write month-end storage outputs for continuity into the next reporting cycle.</li>
        </ol>
        <p class="source-ref">Reference model: Monthly balance engine in <code>services/calculation/balance_service.py</code>.</p>
        <a name="overview-main-pages"></a>
        <h3>Main pages</h3>
        <ul>
            <li><b>Dashboard:</b> Executive snapshot of storage, climate, and closure status.</li>
            <li><b>Analytics:</b> Trend charting from Meter Readings workbook data.</li>
            <li><b>Monitoring:</b> Borehole/static/PCD monitoring review and charting.</li>
            <li><b>Storage Facilities:</b> Facility master data, utilization, and monthly parameters.</li>
            <li><b>Calculations:</b> Monthly closure, recycled water, quality, and days-of-operation outputs.</li>
            <li><b>Flow Diagram:</b> Operational flow categorization and diagram-based closure checks.</li>
            <li><b>Settings:</b> Business constants and monthly rainfall/evaporation controls.</li>
            <li><b>Messages:</b> User notifications, release updates, and feedback intake.</li>
        </ul>
        <a name="overview-data-stores"></a>
        <h3>Primary data stores</h3>
        <ul>
            <li>Monthly climate records (rainfall and evaporation) by year/month.</li>
            <li>Storage facility register and month-to-month storage history tables.</li>
            <li>Flow diagram definitions and flow category mapping data.</li>
            <li>Meter Readings workbook columns used as operational inputs.</li>
        </ul>
        <p class="source-ref">Reference sources: <code>database/*</code>, <code>services/excel_manager.py</code>, <code>ui/dashboards/*.py</code>.</p>
        """

    def _build_dashboards_html(self) -> str:
        return """
        <h2>Dashboard Workflows</h2>
        <a name="dash-analytics"></a>
        <h3>1) Analytics &amp; Trends</h3>
        <ul>
            <li>Select Meter Readings Excel file path.</li>
            <li>Choose chart type, source(s), and date range.</li>
            <li>Generate charts without interrupting normal use of the application.</li>
            <li>Save chart as image/PDF/SVG.</li>
        </ul>
        <p><b>Business outcome:</b> confirms seasonal trends, production-linked usage shifts, and abnormal movement before sign-off.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/analytics_dashboard.py</code>.</p>
        <a name="dash-monitoring"></a>
        <h3>2) Monitoring Data</h3>
        <ul>
            <li>Load folders for Static Boreholes, Borehole Monitoring, or PCD Monitoring.</li>
            <li>System parses and normalizes column names (e.g., Date, Borehole/Point, Aquifer).</li>
            <li>Preview loaded rows in table.</li>
            <li>Filter by year/month/parameter and generate trend charts.</li>
        </ul>
        <p><b>Business outcome:</b> early detection of water-quality or level deviations that can impact operations and compliance.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/monitoring_dashboard.py</code>, <code>services/directory_loader.py</code>.</p>
        <a name="dash-storage"></a>
        <h3>3) Storage Facilities</h3>
        <ul>
            <li>View all storage assets with live capacity and utilization.</li>
            <li>Add/Edit/Delete facilities and set monthly parameters.</li>
            <li>Cards summarize total capacity, current volume, utilization, active count.</li>
        </ul>
        <p><b>Business outcome:</b> supports available-storage planning, transfer decisions, and storage risk visibility.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/storage_facilities_dashboard.py</code>.</p>
        <a name="dash-calculations"></a>
        <h3>4) Calculations</h3>
        <ul>
            <li>Select month/year and run <b>Calculate Balance</b>.</li>
            <li>System checks required data completeness first.</li>
            <li>Results appear in tabs: System Balance, Recycled Water, Data Quality, Days of Operation.</li>
        </ul>
        <p><b>Business outcome:</b> produces auditable closure metrics and highlights reliability before reporting.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/calculation_dashboard.py</code>.</p>
        <a name="dash-flow"></a>
        <h3>5) Flow Diagram</h3>
        <ul>
            <li>Load diagram JSON for selected area.</li>
            <li>Load Excel flow volumes for selected month/year.</li>
            <li>Categorize each edge as Inflow / Outflow / Recirculation / Ignore.</li>
            <li>Balance footer updates using categorized volumes.</li>
        </ul>
        <p><b>Business outcome:</b> reconciles physical process understanding with reported volumes and closure behavior.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/flow_diagram_page.py</code>.</p>
        <a name="dash-settings"></a>
        <h3>6) Settings</h3>
        <ul>
            <li>Constants tab: filter/search constants and update values.</li>
            <li>Environmental tab: load/save monthly rainfall and evaporation values by year.</li>
        </ul>
        <p><b>Business outcome:</b> controlled monthly assumptions and reference data governance.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/settings_dashboard.py</code>.</p>
        """

    def _build_calculations_html(self) -> str:
        return """
        <h2>Calculation Engine</h2>
        <p>
            This page turns monthly inputs into an auditable closure result and operational runway indicators.
        </p>
        <a name="calc-order"></a>
        <h3>Monthly run sequence</h3>
        <ol>
            <li>Calculate all inflow components for the selected month.</li>
            <li>Calculate all outflow components.</li>
            <li>Calculate opening/closing storage and storage change.</li>
            <li>Calculate recycled-water contribution.</li>
            <li>Compute closure error and KPI status.</li>
            <li>Update storage history for continuity into next month.</li>
        </ol>
        <p class="source-ref">Reference engine: <code>services/calculation/balance_service.py</code> (<code>BalanceService.calculate</code>).</p>
        <a name="calc-system-tab"></a>
        <h3>System Balance tab</h3>
        <ul>
            <li>Compares total inflows, total outflows, and storage change.</li>
            <li>Shows closure status and closure error (%).</li>
            <li>Use this tab for monthly reporting sign-off.</li>
        </ul>
        <p class="formula-note"><b>Operations meaning:</b> your primary monthly compliance and governance checkpoint.</p>
        <a name="calc-recycled-tab"></a>
        <h3>Recycled Water tab</h3>
        <ul>
            <li>Uses metered recycled-water total when available in the source workbook.</li>
            <li>If missing, applies configured fallback logic using available return-water indicators.</li>
            <li>Use this tab to explain reuse performance to operations teams.</li>
        </ul>
        <p class="formula-note"><b>Operations meaning:</b> shows whether freshwater demand can be reduced through recovery performance.</p>
        <a name="calc-quality"></a>
        <h3>Data Quality tab</h3>
        <ul>
            <li>Shows missing, estimated, and simulated data flags found during the run.</li>
            <li>Applies scoring rules so users can judge confidence before publishing results.</li>
            <li>High closure error often points to missing fields, mapping gaps, or wrong categorization.</li>
        </ul>
        <p class="formula-note"><b>Operations meaning:</b> confidence gate before results are used for management, audit, or regulatory reporting.</p>
        <a name="calc-days-tab"></a>
        <h3>Days of Operation tab</h3>
        <ul>
            <li><b>What it means:</b> estimated number of days storage can support operations at current average demand.</li>
            <li><b>Monthly usage banner (e.g. 23k m³/month):</b> calculated as <i>Daily Net Fresh Demand × 30</i> for quick planning communication.</li>
            <li><b>System days:</b> total usable storage divided by average daily use.</li>
            <li><b>Facility days:</b> each facility shows its own runway based on that facility's usable volume and share of demand, so values differ by facility.</li>
            <li><b>Source tags:</b> <i>Measured</i> (from month data), <i>History Proxy</i> (from recent pattern), <i>Estimated</i> (fallback rule).</li>
            <li><b>Operational rule:</b> a reserve margin is held back, so displayed days represent usable operating water, not full physical volume.</li>
            <li><b>How to use:</b> prioritize low-day facilities for transfer planning, demand controls, or pumping actions.</li>
        </ul>
        <p class="formula-note"><b>Operations meaning:</b> short-term runway signal for proactive intervention before supply stress.</p>
        <p class="source-ref">Reference: <code>ui/dashboards/calculation_dashboard.py</code>, <code>services/calculation/days_of_operation_service.py</code>.</p>
        """

    def _build_formulas_html(self) -> str:
        worked_example = self._build_live_worked_example_html()
        return """
        <h2>Formulas and Variables</h2>
        <a name="formula-master"></a>
        <h3>1) Balance Closure (what auditors look at)</h3>
        <div class="formula-card" style="padding:10px 12px;">
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Closure Error (m³) = Fresh Inflows - Total Outflows - Storage Change
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:6px 0 2px 0;">
                Closure Error (%) = |Closure Error (m³)| / Fresh Inflows × 100
            </div>
            <p class="formula-note">
                <b>Interpretation:</b> lower is better. Target is typically less than 5%.
            </p>
            <p class="formula-note">
                <b>Operations meaning:</b> this is the monthly reconciliation test. A high value means your water story is incomplete.
            </p>
        </div>

        <h3>2) Rearranged Balance Equation</h3>
        <div class="formula-card" style="padding:10px 12px;">
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Fresh Inflows = Total Outflows + Storage Change + Balance Residual
            </div>
            <p class="formula-note">
                Use this form when explaining where the “missing water” sits.
            </p>
            <p class="formula-note">
                <b>Operations meaning:</b> useful for review meetings when teams ask what must change to close the month.
            </p>
        </div>

        <a name="formula-inflows"></a>
        <h3>3) Inflow Component Formulas</h3>
        <div class="formula-card" style="padding:10px 12px;">
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Rainfall Inflow (m³) = Rainfall (mm) × Active Water Surface Area (m²) ÷ 1000
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Catchment Runoff (m³) = Rainfall (mm) × Catchment Area (m²) × Runoff Coefficient ÷ 1000
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Ore Moisture Inflow (m³) = Tonnes Milled × Ore Moisture Fraction
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Abstraction Inflow (m³) = Total metered abstraction and dewatering for the selected month
            </div>
            <p class="formula-note">
                Example: 200 mm rainfall on 20,000 m² gives <b>4,000 m³</b> rainfall inflow.
            </p>
            <p class="formula-note">
                <b>Operations meaning:</b> these are the main water entries into the system and should reconcile with metered supply reality.
            </p>
        </div>

        <a name="formula-outflows"></a>
        <h3>4) Outflow Component Formulas</h3>
        <div class="formula-card" style="padding:10px 12px;">
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Evaporation Loss (m³) = Monthly evaporation-based facility loss total
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Seepage Loss (m³) = Stored Volume × Seepage Rate (lined or unlined)
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Dust Suppression (m³) = Tonnes Milled × Dust Application Rate (L/t) ÷ 1000
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Tailings Lockup (m³) = Tailings Tonnes × Tailings Moisture Fraction
            </div>
            <p class="formula-note">
                Total Outflow is the sum of all active outflow components for the selected month.
            </p>
            <p class="formula-note">
                <b>Operations meaning:</b> this is where water leaves useful storage and drives replacement demand.
            </p>
        </div>

        <a name="formula-storage"></a>
        <h3>5) Storage Equations</h3>
        <div class="formula-card" style="padding:10px 12px;">
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Closing Storage = Opening Storage + Inflows - Outflows
            </div>
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Storage Change (ΔS) = Closing Storage - Opening Storage
            </div>
            <p class="formula-note">
                If calculated Closing Storage is negative, the system clamps it to 0 and raises a warning.
            </p>
            <p class="formula-note">
                <b>Operations meaning:</b> storage change explains whether the system is drawing down or recovering during the month.
            </p>
        </div>

        <a name="formula-flow"></a>
        <h3>6) Flow Diagram Closure</h3>
        <div class="formula-card" style="padding:10px 12px;">
            <div style="display:block; font-family:'Cambria Math','Times New Roman',serif; font-size:16px; margin:4px 0;">
                Flow Closure Error (%) = |Inflows - Outflows - Recirculation| ÷ Inflows × 100
            </div>
            <p class="formula-note">
                Recirculation is isolated so recycled internal loops are not counted as fresh inflow.
            </p>
            <p class="formula-note">
                <b>Operations meaning:</b> confirms flow-map categorization quality before using diagram closure in technical reviews.
            </p>
        </div>
        <a name="formula-worked"></a>
        <h3>7) Worked Example (live values)</h3>
        """ + worked_example + """

        <h3>Business-to-System Mapping (optional reference)</h3>
        <table class="term-table">
            <tr><th>Business Term</th><th>Code Variable</th><th>Typical Unit</th></tr>
            <tr><td>Fresh Inflows</td><td><code>fresh_inflows_m3</code> / <code>inflows.total_m3</code></td><td>m³</td></tr>
            <tr><td>Total Outflows</td><td><code>outflows_m3</code> / <code>outflows.total_m3</code></td><td>m³</td></tr>
            <tr><td>Storage Change</td><td><code>delta_storage_m3</code> / <code>storage.delta_m3</code></td><td>m³</td></tr>
            <tr><td>Closure Error</td><td><code>balance_error_m3</code></td><td>m³</td></tr>
            <tr><td>Closure Error (%)</td><td><code>error_pct</code></td><td>%</td></tr>
        </table>
        <div class="human-def">
            <b>Unit key:</b> <code>m³</code> = cubic meters, <code>mm</code> = millimeters, <code>L/t</code> = liters per tonne.
        </div>
        <p class="source-ref">Reference: <code>services/calculation/balance_service.py</code>, <code>ui/dashboards/flow_diagram_page.py</code>.</p>
        """

    def _build_live_worked_example_html(self) -> str:
        """Build a business-readable worked example using existing cached results only."""
        try:
            from services.calculation.balance_service import get_balance_service

            service = get_balance_service()
            cache = getattr(service, "_cache", {}) or {}
            if not cache:
                raise ValueError("No cached balance results available")

            # Use the most recently inserted cached result to avoid recomputation side effects.
            result = list(cache.values())[-1]

            inflows = float(result.inflows.total_m3 or 0.0)
            outflows = float(result.outflows.total_m3 or 0.0)
            delta_s = float(result.storage.delta_m3 or 0.0)
            err_m3 = float(result.balance_error_m3 or 0.0)
            err_pct = float(abs(result.error_pct or 0.0))
            period_label = result.period.period_label
            status = "Balanced" if err_pct < 5 else "Needs review"
            status_color = "#1d7f37" if err_pct < 5 else "#b54708"

            return f"""
            <div class="formula-card">
                <p><b>Period:</b> {escape(period_label)} &nbsp;&nbsp; <b>Status:</b> <span style="color:{status_color};">{status}</span></p>
                <span class="eqn">Closure Error (m³) = {inflows:,.0f} - {outflows:,.0f} - {delta_s:,.0f} = {err_m3:,.0f}</span>
                <span class="eqn">Closure Error (%) = |{err_m3:,.0f}| ÷ {max(inflows, 1):,.0f} × 100 = {err_pct:.2f}%</span>
                <p class="formula-note">
                    <b>Reading:</b> this uses the latest calculated result already available in this session and shows how closure is produced.
                </p>
            </div>
            """
        except Exception:
            return """
            <div class="formula-card">
                <p><b>Worked example unavailable.</b></p>
                <p class="formula-note">
                    Run <b>Calculations → Calculate Balance</b> first, then return to this tab to see a numeric substitution from your latest result.
                </p>
                <span class="eqn">Example pattern: Closure Error (m³) = Fresh Inflows - Total Outflows - Storage Change</span>
                <span class="eqn">Closure Error (%) = |Closure Error (m³)| ÷ Fresh Inflows × 100</span>
            </div>
            """

    def _build_water_sources_html(self) -> str:
        surface = self._format_list(EXCEL_COLUMNS.get("surface_water_sources", []))
        groundwater = self._format_list(EXCEL_COLUMNS.get("groundwater_sources", []))
        dewatering = self._format_list(EXCEL_COLUMNS.get("dewatering_sources", []))
        return f"""
        <h2>Water Sources and Data Inputs</h2>
        <a name="sources-env"></a>
        <h3>Climate Inputs (Settings - Environmental)</h3>
        <ul>
            <li>Monthly rainfall drives rainfall inflow.</li>
            <li>Monthly evaporation drives evaporation loss.</li>
            <li>If either is missing for the selected month, closure quality can degrade.</li>
        </ul>
        <a name="sources-storage-db"></a>
        <h3>Storage Inputs (Facility register and history)</h3>
        <ul>
            <li>Surface area scales rain and evaporation effect by facility.</li>
            <li>Current volume and history support opening/closing storage continuity.</li>
            <li>Inactive facilities are excluded from operational totals.</li>
        </ul>
        <a name="sources-excel"></a>
        <h3>Meter Readings Workbook (key fields)</h3>
        <ul>
            <li><code>{escape(str(EXCEL_COLUMNS.get("tonnes_milled", "Tonnes Milled")))}</code></li>
            <li><code>{escape(str(EXCEL_COLUMNS.get("total_consumption", "Total Water Consumption")))}</code></li>
            <li><code>{escape(str(EXCEL_COLUMNS.get("total_recycled", "Total Recycled Water")))}</code></li>
            <li><code>{escape(str(EXCEL_COLUMNS.get("rwd_1", "RWD")))}</code> (volume m³)</li>
            <li><code>{escape(str(EXCEL_COLUMNS.get("rwd_intensity", "RWD.1")))}</code> (intensity indicator)</li>
            <li><code>{escape(str(EXCEL_COLUMNS.get("tailings_density", "Tailings RD")))}</code> (tailings density input)</li>
        </ul>
        <h3>Surface Water Inflow Fields</h3>
        <a name="sources-surface"></a>
        {surface}
        <h3>Groundwater Inflow Fields</h3>
        <a name="sources-ground"></a>
        {groundwater}
        <h3>Dewatering Fields</h3>
        <a name="sources-dewater"></a>
        {dewatering}
        <h3>If your workbook layout is different</h3>
        <ul>
            <li>Analytics and Monitoring are tolerant of many naming variants.</li>
            <li>Calculations still require essential meter fields (or approved mappings).</li>
            <li>Flow Diagram values depend on configured sheet/column mapping for each flow.</li>
        </ul>
        <h3>Business controls</h3>
        <ul>
            <li>Treat workbook templates as controlled inputs to avoid month-to-month column drift.</li>
            <li>When source files change structure, remap first before running sign-off calculations.</li>
            <li>Use Data Quality tab to confirm critical fields were found and consumed.</li>
        </ul>
        <p class="source-ref">Reference: <code>services/calculation/balance_service.py</code>, <code>services/excel_manager.py</code>.</p>
        """

    def _build_storage_html(self) -> str:
        return """
        <h2>Storage Logic</h2>
        <a name="storage-opening-closing"></a>
        <h3>Opening and closing rule</h3>
        <ul>
            <li>Opening volume comes from the prior month closing record when available.</li>
            <li>If prior history is missing, a controlled fallback uses current facility volume and marks quality risk.</li>
            <li>Closing storage is calculated after monthly inflows and outflows are applied.</li>
        </ul>
        <a name="storage-persistence"></a>
        <h3>Month-end continuity</h3>
        <ul>
            <li>Each calculation run stores a month-end storage snapshot.</li>
            <li>Latest closing storage updates the facility current-volume value.</li>
            <li>Storage dashboard then reflects updated month-end state for operations.</li>
        </ul>
        <a name="storage-warnings"></a>
        <h3>Warnings and safeguards</h3>
        <ul>
            <li>Negative calculated closing is clamped to zero.</li>
            <li>Capacity exceedance is flagged for review.</li>
            <li>Large month-to-month jumps should be checked against transfer records and meter data.</li>
        </ul>
        <h3>Business interpretation</h3>
        <ul>
            <li><b>Utilization (%)</b> is operating fullness, not design safety margin.</li>
            <li>High utilization plus low days-of-operation runway can indicate supply risk.</li>
            <li>Use storage trends together with flow and quality tabs before operational decisions.</li>
        </ul>
        <p class="source-ref">Reference: <code>services/calculation/balance_service.py</code> (<code>StorageService</code>).</p>
        """

    def _build_features_html(self) -> str:
        return """
        <h2>Platform Features</h2>
        <a name="features-performance"></a>
        <ul>
            <li><b>Smooth loading:</b> heavy chart/data loading runs asynchronously so pages stay responsive.</li>
            <li><b>Session-safe flow loading:</b> Flow Diagram clears persisted volumes until Excel is explicitly loaded in current session.</li>
            <li><b>Recirculation manager:</b> Configure recirculation entries and load recirculation volumes for selected month/year.</li>
            <li><b>Fast repeat runs:</b> monthly results are cached unless a fresh recalculation is requested.</li>
            <li><b>Export:</b> Charts can be saved (image/PDF/SVG where available).</li>
            <li><b>Data quality flags:</b> Missing and estimated values are tracked and surfaced in results.</li>
        </ul>
        <p class="source-ref">Reference: <code>ui/dashboards/analytics_dashboard.py</code>, <code>ui/dashboards/monitoring_dashboard.py</code>, <code>ui/dashboards/flow_diagram_page.py</code>, <code>services/calculation/balance_service.py</code>.</p>
        """

    def _build_troubleshooting_html(self) -> str:
        return """
        <h2>Troubleshooting</h2>
        <a name="trouble-common"></a>
        <h3>Common operational issues</h3>
        <ul>
            <li><b>No values after loading page:</b> load Excel in current session (Flow Diagram keeps values zero until then).</li>
            <li><b>High closure error (&gt;5%):</b> review flow categorization, missing intake/loss values, and climate data for that month.</li>
            <li><b>Calculation warnings:</b> check Data Quality tab for missing or estimated fields.</li>
            <li><b>Zero rainfall/evaporation:</b> confirm year/month entries in Settings → Environmental.</li>
            <li><b>Storage anomalies:</b> verify active facilities, capacities, and storage history continuity.</li>
            <li><b>Monitoring charts empty:</b> confirm the selected parameter is numeric and date/location fields loaded correctly.</li>
        </ul>
        <p class="formula-note"><b>Operations meaning:</b> most closure problems come from data readiness and mapping, not the math engine.</p>
        <a name="trouble-checklist"></a>
        <h3>Pre-run checklist</h3>
        <ol>
            <li>Meter Readings Excel path is selected and file exists.</li>
            <li>Required Meter Reading fields are present for the month.</li>
            <li>Environmental monthly data exists for selected period.</li>
            <li>At least one active storage facility is configured.</li>
            <li>Flow Diagram mapping is configured (if you use diagram-based balance checks).</li>
        </ol>
        <p class="formula-note"><b>Operations meaning:</b> completing this checklist before month-end run reduces rework and late sign-off risk.</p>
        <h3>Closure targets</h3>
        <a name="trouble-targets"></a>
        <ul>
            <li>&lt; 5%: generally acceptable closure quality.</li>
            <li>5% to 10%: review mappings and assumptions.</li>
            <li>&gt; 10%: investigate categorization and missing data before sign-off.</li>
        </ul>
        <p class="formula-note"><b>Operations meaning:</b> treat closure bands as decision thresholds for escalation, not just display colors.</p>
        <h3>Recommended action path</h3>
        <ol>
            <li>Fix missing source fields first.</li>
            <li>Recheck flow categories and mappings.</li>
            <li>Re-run calculations for the same month.</li>
            <li>Confirm Data Quality and closure thresholds before sign-off.</li>
        </ol>
        <p class="formula-note"><b>Operations meaning:</b> this sequence is the fastest route to a stable, defensible month-end result.</p>
        <p class="source-ref">Reference: <code>services/calculation/balance_service.py</code>, <code>ui/dashboards/flow_diagram_page.py</code>, <code>ui/dashboards/calculation_dashboard.py</code>.</p>
        """

    @staticmethod
    def _format_list(values: list[str]) -> str:
        if not values:
            return "<p><i>No configured entries found.</i></p>"
        items = "".join(f"<li><code>{escape(str(item))}</code></li>" for item in values)
        return f"<ul>{items}</ul>"
