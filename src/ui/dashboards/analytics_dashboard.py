"""
Analytics & Trends page controller (PySide6).

Purpose:
- Load the compiled Designer UI from generated_ui_analytics.py
- Handle file selection for the Meter Readings Excel path
- Render a placeholder chart in the chart area using QtCharts (if available)
- Keep all logic out of the generated UI for maintainability

Notes:
- This controller only wires UI events and draws a simple chart for now.
  Real data binding can be added later via services.
- The chart area uses `chartViewport` as a host widget; we dynamically
  insert/remove a `QChartView` at runtime.
"""

from __future__ import annotations

from datetime import date
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import (
    Qt,
    QDate,
    QDateTime,
    QTime,
    QRect,
    QSize,
    QSizeF,
    QThread,
    Signal,
    QObject,
    QTimer,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPdfWriter, QPageSize, QCursor, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QLabel,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QAbstractItemView,
    QApplication,
    QSizePolicy,
)

# QtCharts is part of PySide6-Addons; import conditionally
try:  # pragma: no cover - optional addon
    from PySide6.QtCharts import (
        QChart,
        QChartView,
        QLineSeries,
        QAreaSeries,
        QSplineSeries,
        QScatterSeries,
        QBarSeries,
        QBarSet,
        QStackedBarSeries,
        QCategoryAxis,
        QBarCategoryAxis,
        QValueAxis,
        QDateTimeAxis,
    )

    HAS_QTCHARTS = True
except Exception:  # pragma: no cover
    QChart = QChartView = QLineSeries = None
    QAreaSeries = QSplineSeries = QScatterSeries = None
    QBarSeries = QBarSet = QStackedBarSeries = None
    QCategoryAxis = QBarCategoryAxis = QValueAxis = QDateTimeAxis = None
    HAS_QTCHARTS = False

# QtSvg is optional; only needed for SVG export
try:  # pragma: no cover - optional addon
    from PySide6.QtSvg import QSvgGenerator

    HAS_QTSVG = True
except Exception:  # pragma: no cover
    QSvgGenerator = None
    HAS_QTSVG = False

from .generated_ui_analytics import Ui_Form
from services.excel_manager import get_excel_manager
from core.app_logger import logger as app_logger
from ui.theme import PALETTE


class ChartDataWorker(QObject):
    """Background worker to load chart data without blocking the UI.

    This worker performs Excel I/O in a QThread and returns a cache of
    series data keyed by source name. UI updates and chart rendering
    remain on the main thread for Qt safety.
    """

    started = Signal()
    progress = Signal(str)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        excel_manager,
        selected_sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        logger,
    ) -> None:
        """Initialize the worker with Excel manager and selection context.

        Args:
            excel_manager: ExcelManager instance for Meter Readings access.
            selected_sources: List of source names selected by the user.
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            logger: Dashboard logger for background diagnostics.
        """
        super().__init__()
        self._excel_manager = excel_manager
        self._selected_sources = selected_sources
        self._start_date = start_date
        self._end_date = end_date
        self._logger = logger

    def run(self) -> None:
        """Load series data for selected sources in the background.

        Emits:
            finished: Dict with 'series_cache' and 'loaded_sources'.
            failed: Error string if any exception occurs.
        """
        self.started.emit()

        try:
            series_cache: Dict[str, List[Tuple[date, float]]] = {}
            loaded_sources: List[str] = []

            for idx, source_name in enumerate(self._selected_sources, start=1):
                # Progress update for long-running Excel reads
                self.progress.emit(
                    f"Loading {source_name} ({idx}/{len(self._selected_sources)})..."
                )

                # Read series from Meter Readings Excel (data source clarity)
                series_data = self._excel_manager.get_meter_readings_series(
                    source_name=source_name,
                    start_date=self._start_date,
                    end_date=self._end_date,
                )

                if series_data:
                    series_cache[source_name] = series_data
                    loaded_sources.append(source_name)

            self._logger.info(
                "Chart data loaded in background",
                extra={"sources": loaded_sources, "count": len(series_cache)},
            )

            self.finished.emit(
                {
                    "series_cache": series_cache,
                    "loaded_sources": loaded_sources,
                }
            )
        except Exception as exc:
            self._logger.error("Chart data worker failed", exc_info=True)
            self.failed.emit(str(exc))


class AnalyticsPage(QWidget):
    """Analytics & Trends page (KPI charts & trends).

    Responsibilities:
    - Own the page widget and its runtime behavior
    - Provide file selection UX and basic validation
    - Draw a simple chart into `chartViewport` when the user clicks Generate

    UI contract (selected elements):
    - `select_file_button`: opens file dialog
    - `line_edit_folder_path`: shows selected file path
    - `generate_chart`: plots a simple series in the chart area
    - `chartLayout`: VBoxLayout that hosts the chart view
    - `label_chartplaceholder`: pre-chart message that we hide once a chart renders
    - Collapse/expand: wired by Designer via `toggled` signals
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._apply_title_icon()

        # Dashboard-specific logger (logs/analytics/)
        self.logger = app_logger.get_dashboard_logger("analytics")
        # Ensure analytics folder exists by calling logger
        self.logger.info("Analytics dashboard initializing...")

        # Async chart worker state (QThread-based, non-blocking UI)
        self._chart_thread: Optional[QThread] = None
        self._chart_worker: Optional[ChartDataWorker] = None
        self._series_cache: Optional[Dict[str, List[Tuple[date, float]]]] = None
        self._pending_chart_context: Optional[Dict[str, object]] = None

        # Status label for user feedback during background loading
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("")

        # Excel manager for user-defined paths (persisted in config)
        self._excel_manager = get_excel_manager()

        # Remove the bottom vertical spacer to let chart use full space
        # (Generated UI adds a spacer that we don't want)
        spacer_item = self.ui.verticalLayout.itemAt(self.ui.verticalLayout.count() - 1)
        if spacer_item and spacer_item.spacerItem():
            self.ui.verticalLayout.removeItem(spacer_item)

        # Insert status label at top of the chart layout for progress visibility
        if hasattr(self.ui, "chartLayout"):
            self.ui.chartLayout.insertWidget(0, self._status_label)

        # Remove the DataSource file-section spacer to reduce extra vertical padding
        # (generated UI inserts a vertical spacer inside the file section layout)
        if hasattr(self.ui, "verticalLayout_frame_content"):
            for idx in range(self.ui.verticalLayout_frame_content.count() - 1, -1, -1):
                item = self.ui.verticalLayout_frame_content.itemAt(idx)
                if item and item.spacerItem():
                    self.ui.verticalLayout_frame_content.removeItem(item)

        # Remove chart-options spacer that can waste vertical space on smaller screens
        # (generated UI inserts a vertical spacer inside the chart options layout)
        if hasattr(self.ui, "verticalLayout_chart_options"):
            for idx in range(self.ui.verticalLayout_chart_options.count() - 1, -1, -1):
                item = self.ui.verticalLayout_chart_options.itemAt(idx)
                if item and item.spacerItem():
                    self.ui.verticalLayout_chart_options.removeItem(item)

        # Slightly increase the chart area's vertical presence without resizing the window.
        # Use a responsive minimum height so laptop screens still fit the layout.
        screen = QApplication.primaryScreen()
        screen_height = screen.availableGeometry().height() if screen else 900
        responsive_height = int(screen_height * 0.45)
        self._chart_min_height = max(320, min(responsive_height, 520))
        if hasattr(self.ui, "label_chartplaceholder"):
            self.ui.label_chartplaceholder.setMinimumHeight(self._chart_min_height)

        # Hook up actions
        self.ui.select_file_button.clicked.connect(self._on_select_file)
        self.ui.generate_chart.clicked.connect(self._on_generate_chart)
        self.ui.save_chart.clicked.connect(self._on_save_chart)

        # Update chart type availability when source selection changes
        self.ui.water_source_options.currentTextChanged.connect(self._on_source_changed)

        # DataSource section collapse/expand (make button checkable)
        self.ui.pushButton.setCheckable(True)
        self.ui.pushButton.setChecked(False)  # Start collapsed
        self.ui.pushButton.clicked.connect(self._on_toggle_datasource_section)

        # Chart options collapse/expand (tighten space when collapsed)
        self.ui.chart_options_logo_2.toggled.connect(self._on_toggle_chart_options)
        self._on_toggle_chart_options(self.ui.chart_options_logo_2.isChecked())

        # Override chart options from UI with supported time-series types
        self._load_chart_type_options()

        # Track the current chart view so we can replace it cleanly
        self._chart_view: Optional[QChartView] = None

        # Track multi-select sources for comparison charts
        self._selected_sources: List[str] = []

        # Clear saved Meter Readings path only in release builds
        if getattr(sys, "frozen", False):
            self._reset_meter_readings_state()
        else:
            self._apply_saved_meter_readings_path()

        # Populate UI selections from Excel (if available)
        self._refresh_meter_readings_metadata()

        # Add a dedicated multi-select UI control
        self._add_multi_select_button()
        # Tighten chart options spacing and align controls into a compact grid
        self._apply_compact_chart_options_layout()
        self._enforce_action_button_visibility()

        # Expand the DataSource section when no file is loaded
        exists, _ = self._excel_manager.meter_readings_status()
        if exists:
            self._collapse_datasource_section()
        else:
            self._expand_datasource_section()

    def _apply_saved_meter_readings_path(self) -> None:
        """Populate the file path field from saved config (if present).

        This ensures the user-selected path is remembered across sessions.
        """
        exists, path = self._excel_manager.meter_readings_status()
        if exists:
            self.ui.line_edit_folder_path.setText(str(path))
        else:
            self.ui.line_edit_folder_path.setText("")
        self.ui.line_edit_folder_path.setStyleSheet("")

    def _reset_meter_readings_state(self) -> None:
        self._excel_manager.set_meter_readings_path("")
        self.ui.line_edit_folder_path.setText("")
        self.ui.line_edit_folder_path.setStyleSheet("")
        self._set_header_counts(records=0, sources=0)
        self._selected_sources = []
        self._series_cache = None

    def _refresh_meter_readings_metadata(self) -> None:
        """Load sources/date ranges from Excel and update UI controls.

        This reads Meter Readings metadata using ExcelManager and updates:
        - water_source_options
        - year/month filters
        - records_loaded_2 / sources_loaded_2 labels
        """
        exists, _ = self._excel_manager.meter_readings_status()
        if not exists:
            self._set_header_counts(records=0, sources=0)
            return

        df = self._excel_manager.load_meter_readings()
        sources = self._excel_manager.list_meter_readings_sources()
        min_date, max_date = self._excel_manager.get_meter_readings_date_range()

        # Update header stats
        self._set_header_counts(records=len(df), sources=len(sources))

        # Populate sources
        self.ui.water_source_options.clear()
        if sources:
            # Add "All Sources" for multi-series view
            self.ui.water_source_options.addItem("All Sources")
            self.ui.water_source_options.addItems(sources)
        # Keep combo read-only; dedicated multi-select is handled via dialog
        self.ui.water_source_options.setEditable(False)

        # Reset custom selections if the source list changes
        self._selected_sources = []

        # Populate year/month filters if we have date range
        if min_date and max_date:
            years = [str(y) for y in range(min_date.year, max_date.year + 1)]
            months = [f"{m:02d}" for m in range(1, 13)]

            self.ui.year_from.clear()
            self.ui.year_to.clear()
            self.ui.month_from.clear()
            self.ui.month_to.clear()

            self.ui.year_from.addItem("")
            self.ui.year_to.addItem("")
            self.ui.month_from.addItem("")
            self.ui.month_to.addItem("")

            self.ui.year_from.addItems(years)
            self.ui.year_to.addItems(years)
            self.ui.month_from.addItems(months)
            self.ui.month_to.addItems(months)

    def _set_header_counts(self, records: int, sources: int) -> None:
        """Update record/source counters in the header area."""
        self.ui.records_loaded_2.setText(f"{records} records")
        self.ui.sources_loaded_2.setText(f"{sources} sources loaded")

    def _on_toggle_datasource_section(self) -> None:
        """Toggle DataSource section visibility (collapse/expand)."""
        if self.ui.pushButton.isChecked():
            self._expand_datasource_section()
        else:
            self._collapse_datasource_section()

    def _collapse_datasource_section(self) -> None:
        """Collapse the DataSource file selection area (hide UI elements)."""
        self.ui.line_edit_folder_path.setVisible(False)
        self.ui.select_file_button.setVisible(False)
        self.ui.pushButton.setText("DataSource File (collapsed)")
        self.ui.pushButton.setChecked(False)

    def _expand_datasource_section(self) -> None:
        """Expand the DataSource file selection area (show UI elements)."""
        self.ui.line_edit_folder_path.setVisible(True)
        self.ui.select_file_button.setVisible(True)
        self.ui.pushButton.setText("DataSource File")
        self.ui.pushButton.setChecked(True)

    def _on_toggle_chart_options(self, checked: bool) -> None:
        """Collapse chart options frame to remove reserved space."""
        frame = self.ui.frame_2
        frame.setVisible(checked)
        if checked:
            frame.setMaximumHeight(16777215)
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            frame.setMaximumHeight(0)
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _add_multi_select_button(self) -> None:
        """Insert a dedicated multi-select button into the chart options row.

        This allows users to choose multiple sources without typing comma lists.
        """
        button = QPushButton("Multi-select")
        button.setObjectName("btn_multi_select_sources")
        button.setMinimumWidth(120)
        button.setIcon(QIcon(":/icons/multi_select_button.svg"))
        button.setIconSize(QSize(14, 14))
        button.clicked.connect(self._open_multi_select_dialog)

        # Insert next to the water source combo (before spacer)
        layout = self.ui.horizontalLayout_chart_type
        insert_index = max(0, layout.count() - 1)
        layout.insertWidget(insert_index, button)

    def _apply_compact_chart_options_layout(self) -> None:
        """Reflow chart options into two compact rows with predictable spacing."""
        if not hasattr(self.ui, "verticalLayout_chart_options"):
            return

        options_layout = self.ui.verticalLayout_chart_options
        options_layout.setContentsMargins(12, 8, 12, 8)
        options_layout.setSpacing(4)

        # Move widgets from the existing layouts into a 2-row grid.
        chart_type_layout = getattr(self.ui, "horizontalLayout_chart_type", None)
        date_range_layout = getattr(self.ui, "horizontalLayout_date_range", None)

        widgets_by_name = {}
        for layout in [chart_type_layout, date_range_layout]:
            if not layout:
                continue
            options_layout.removeItem(layout)
            for idx in range(layout.count() - 1, -1, -1):
                item = layout.takeAt(idx)
                if item and item.widget():
                    widget = item.widget()
                    widgets_by_name[widget.objectName()] = widget

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)
        for name in [
            "label_chart_type",
            "charts_options",
            "water_source_label",
            "water_source_options",
            "btn_multi_select_sources",
        ]:
            widget = widgets_by_name.get(name)
            if widget is not None:
                top_row.addWidget(widget)
        top_row.addStretch(1)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(6)
        for name in [
            "date_range_label",
            "label_from",
            "year_from",
            "month_label",
            "month_from",
        ]:
            widget = widgets_by_name.get(name)
            if widget is not None:
                bottom_row.addWidget(widget)
        bottom_row.addSpacing(12)
        for name in [
            "label_to_year",
            "year_to",
            "to_month_label",
            "month_to",
        ]:
            widget = widgets_by_name.get(name)
            if widget is not None:
                bottom_row.addWidget(widget)
        buttons_layout = getattr(self.ui, "horizontalLayout_buttons", None)
        if buttons_layout:
            options_layout.removeItem(buttons_layout)
            action_widgets = []
            for idx in range(buttons_layout.count() - 1, -1, -1):
                item = buttons_layout.takeAt(idx)
                if item and item.widget():
                    action_widgets.insert(0, item.widget())
            if action_widgets:
                bottom_row.addSpacing(20)
                for button in action_widgets:
                    bottom_row.addWidget(button)

        bottom_row.addStretch(1)

        options_layout.insertLayout(0, top_row)
        options_layout.insertLayout(1, bottom_row)

        # Keep date controls visually tight and predictable.
        for combo in [self.ui.year_from, self.ui.month_from, self.ui.year_to, self.ui.month_to]:
            combo.setFixedWidth(98)
            combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            combo.setMinimumHeight(23)
        for combo in [self.ui.charts_options, self.ui.water_source_options]:
            combo.setFixedWidth(140)
            combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            combo.setMinimumHeight(23)
        self.ui.label_from.setText("From Year:")

    def _enforce_action_button_visibility(self) -> None:
        """Ensure action button text stays readable regardless of stylesheet clashes."""
        self.ui.generate_chart.setText("Generate Chart")
        self.ui.save_chart.setText("Save Chart")

    def _apply_title_icon(self) -> None:
        """Render analytics title with dedicated icon (no emoji fallback)."""
        if not hasattr(self.ui, "label_title") or not hasattr(self.ui, "verticalLayout"):
            return

        old_title_label = self.ui.label_title
        title_label = QLabel("Analytics & Trends")
        title_label.setObjectName("label_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_label.setMinimumHeight(34)
        title_label.setMaximumHeight(16777215)
        title_label.setWordWrap(False)
        title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        row = QWidget(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        icon_label = QLabel(row)
        icon_label.setPixmap(QIcon(":/icons/analytics-chart_analytics_title PAge.svg").pixmap(24, 24))
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        row_layout.addStretch(1)

        self.ui.verticalLayout.replaceWidget(old_title_label, row)
        old_title_label.hide()
        old_title_label.setParent(None)
        if hasattr(self.ui, "label_subtitle"):
            self.ui.label_subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.label_subtitle.setContentsMargins(0, 0, 0, 2)
        self.ui.generate_chart.setMinimumWidth(150)
        self.ui.save_chart.setMinimumWidth(130)
        self.ui.generate_chart.setMinimumHeight(30)
        self.ui.generate_chart.setMaximumHeight(30)
        self.ui.save_chart.setMinimumHeight(30)
        self.ui.save_chart.setMaximumHeight(30)
        self.ui.generate_chart.setIcon(QIcon(":/icons/chart_white.svg"))
        self.ui.generate_chart.setIconSize(QSize(14, 14))
        self.ui.save_chart.setIcon(QIcon(":/icons/save_icon_black.svg"))
        self.ui.save_chart.setIconSize(QSize(14, 14))
        self.ui.generate_chart.setStyleSheet(
            "background-color:#1f3a5f; color:#ffffff; border:1px solid #1f3a5f; "
            "border-radius:8px; padding:6px 12px; font-weight:700;"
        )
        self.ui.save_chart.setStyleSheet(
            "background-color:#ffffff; color:#1f2f43; border:1px solid #c7d0da; "
            "border-radius:8px; padding:6px 12px; font-weight:600;"
        )

    def _open_multi_select_dialog(self) -> None:
        """Open a modal dialog to select multiple sources.

        Selected sources are stored in `_selected_sources` and displayed
        as a "Custom Selection" option in the combo.
        """
        sources = self._excel_manager.list_meter_readings_sources()
        if not sources:
            QMessageBox.information(
                self,
                "No Sources",
                "Load Meter Readings data before selecting sources.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Water Sources")
        dialog.setModal(True)

        list_widget = QListWidget(dialog)
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        for src in sources:
            item = QListWidgetItem(src)
            if src in self._selected_sources:
                item.setSelected(True)
            list_widget.addItem(item)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout = QVBoxLayout(dialog)
        layout.addWidget(list_widget)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected = [item.text() for item in list_widget.selectedItems()]
        self._selected_sources = selected
        self._set_custom_selection_label(selected)

    def _set_custom_selection_label(self, selected: List[str]) -> None:
        """Update combo box to reflect a custom multi-source selection."""
        if not selected:
            self.ui.water_source_options.setCurrentIndex(0)
            return

        # If user selected all sources, use built-in "All Sources" option
        all_sources = self._excel_manager.list_meter_readings_sources()
        if set(selected) == set(all_sources) and all_sources:
            idx = self.ui.water_source_options.findText("All Sources")
            if idx >= 0:
                self.ui.water_source_options.setCurrentIndex(idx)
            return

        # Use or add a "Custom Selection" label for multi-source comparisons
        label = f"Custom Selection ({len(selected)})"
        existing = self.ui.water_source_options.findText(label)
        if existing < 0:
            self.ui.water_source_options.addItem(label)
            existing = self.ui.water_source_options.findText(label)
        self.ui.water_source_options.setCurrentIndex(existing)

    def _on_select_file(self) -> None:
        """Open a file dialog and populate the path field.

        Behavior:
        - Allows choosing .xlsx/.xls files (Meter Readings Excel)
        - Shows path in `line_edit_folder_path`
        - Simple existence validation
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Meter Readings Excel",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)",
        )
        if not path:
            return

        # Persist user-selected path so it is remembered next session
        self._excel_manager.set_meter_readings_path(path)
        self._apply_saved_meter_readings_path()
        self._refresh_meter_readings_metadata()

    def _ensure_meter_readings_path(self) -> bool:
        """Ensure Meter Readings path is configured and exists.

        If missing, prompt user to select the file and persist the path.

        Returns:
            True if a valid path exists after prompting; False otherwise.
        """
        exists, _ = self._excel_manager.meter_readings_status()
        if exists:
            return True

        # Prompt user to select the file when missing
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Meter Readings Excel",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)",
        )
        if not path:
            self._apply_saved_meter_readings_path()
            return False

        self._excel_manager.set_meter_readings_path(path)
        self._apply_saved_meter_readings_path()
        self._refresh_meter_readings_metadata()
        return True

    def _on_source_changed(self, text: str) -> None:
        """Update chart type options when source selection changes.

        Disables Bar Chart for multi-source selections (Custom Selection)
        since Bar Chart only works with single sources.
        """
        is_multi_select = "Custom Selection" in text or text == "All Sources"

        # Find Bar Chart item index
        for i in range(self.ui.charts_options.count()):
            if self.ui.charts_options.itemText(i) == "Bar Chart":
                # Get the model to enable/disable the item
                model = self.ui.charts_options.model()
                item = model.item(i)
                if is_multi_select:
                    # Disable Bar Chart for multi-select
                    item.setEnabled(False)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                else:
                    # Enable Bar Chart for single source
                    item.setEnabled(True)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                break

    def _on_generate_chart(self) -> None:
        """Render a simple chart in the viewport (placeholder demo).

        Uses QtCharts if available; otherwise shows the placeholder label.
        Uses a background worker to prevent UI freezing.
        """
        # Prevent starting multiple concurrent workers
        if self._chart_thread and self._chart_thread.isRunning():
            QMessageBox.information(
                self,
                "Chart Generation",
                "A chart is already being generated. Please wait for it to finish.",
            )
            return

        self.logger.info("Chart generation requested (async)")
        self._start_chart_generation_async()

    def _start_chart_generation_async(self) -> None:
        """Start chart data loading in a background QThread.

        This method validates the user selections on the UI thread, then
        delegates Excel I/O to a worker thread for responsiveness.
        """
        # Ensure the Meter Readings path is configured before rendering
        if not self._ensure_meter_readings_path():
            return
        if not HAS_QTCHARTS:
            self.ui.label_chartplaceholder.setText(
                "QtCharts not available. Install PySide6-Addons to enable charts."
            )
            self.ui.label_chartplaceholder.setAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            )
            return

        raw_source = self.ui.water_source_options.currentText().strip()
        if not raw_source:
            QMessageBox.warning(self, "Missing Source", "Please select a water source.")
            return

        selected_sources = self._get_selected_sources(raw_source)
        if not selected_sources:
            QMessageBox.warning(
                self,
                "Missing Source",
                "Please select at least one water source.",
            )
            return

        start_date, end_date = self._get_selected_date_range()
        chart_type = self.ui.charts_options.currentText().strip()
        title = self._build_chart_title(raw_source, start_date, end_date, chart_type)
        y_label = self._build_y_axis_label(raw_source)

        # Store context to keep chart rendering consistent with current selection
        self._pending_chart_context = {
            "raw_source": raw_source,
            "selected_sources": selected_sources,
            "start_date": start_date,
            "end_date": end_date,
            "chart_type": chart_type,
            "title": title,
            "y_label": y_label,
        }

        # Initialize worker and thread
        self._chart_worker = ChartDataWorker(
            excel_manager=self._excel_manager,
            selected_sources=selected_sources,
            start_date=start_date,
            end_date=end_date,
            logger=self.logger,
        )
        self._chart_thread = QThread(self)
        self._chart_worker.moveToThread(self._chart_thread)

        # Connect worker lifecycle signals
        self._chart_thread.started.connect(self._chart_worker.run)
        self._chart_worker.progress.connect(self._on_chart_worker_progress)
        self._chart_worker.finished.connect(self._on_chart_data_ready)
        self._chart_worker.failed.connect(self._on_chart_worker_error)

        # Ensure cleanup when thread finishes
        self._chart_worker.finished.connect(self._chart_thread.quit)
        self._chart_worker.failed.connect(self._chart_thread.quit)
        self._chart_thread.finished.connect(self._clear_chart_worker)

        # Visual feedback for users
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        self._set_chart_status("Loading chart data...", is_error=False)

        self._chart_thread.start()

    def _on_chart_worker_progress(self, message: str) -> None:
        """Update status label from background worker progress signals."""
        self._set_chart_status(message, is_error=False)

    def _on_chart_data_ready(self, payload: Dict[str, object]) -> None:
        """Render chart on the UI thread after background data load completes.

        Args:
            payload: Dict with keys 'series_cache' and 'loaded_sources'.
        """
        try:
            context = self._pending_chart_context or {}
            selected_sources = context.get("selected_sources", [])
            chart_type = context.get("chart_type", "")
            raw_source = context.get("raw_source", "")
            start_date = context.get("start_date")
            end_date = context.get("end_date")
            title = context.get("title", "")
            y_label = context.get("y_label", "Value")

            series_cache = payload.get("series_cache", {})
            self._series_cache = series_cache

            # Validate multi-source constraints before rendering
            if chart_type == "Stacked Bar" and len(selected_sources) <= 1:
                QMessageBox.information(
                    self,
                    "Not Supported",
                    "Stacked charts require multiple sources. Select 'All Sources' or add more.",
                )
                return

            # Build chart based on source count
            if len(selected_sources) > 1:
                chart = self._build_multi_series_chart(
                    selected_sources=selected_sources,
                    start_date=start_date,
                    end_date=end_date,
                    chart_type=chart_type,
                    title=title,
                    raw_source_name=raw_source,
                )
            else:
                source_name = selected_sources[0]
                series_data = self._get_series_data(
                    source_name=source_name,
                    start_date=start_date,
                    end_date=end_date,
                )
                if not series_data:
                    QMessageBox.information(
                        self,
                        "No Data",
                        "No data available for the selected source/date range.",
                    )
                    return

                # Use actual data range for title accuracy
                actual_start = min(d for d, _ in series_data)
                actual_end = max(d for d, _ in series_data)
                actual_range = (actual_start, actual_end)
                title = self._build_chart_title(
                    raw_source,
                    start_date,
                    end_date,
                    chart_type,
                    actual_data_range=actual_range,
                )

                chart = self._build_single_series_chart(
                    series_data=series_data,
                    source_name=source_name,
                    chart_type=chart_type,
                    title=title,
                    y_label=y_label,
                )

            # Replace any existing chart view
            if self._chart_view is not None:
                self.ui.chartLayout.removeWidget(self._chart_view)
                self._chart_view.deleteLater()
                self._chart_view = None

            self._chart_view = QChartView(chart)
            self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Set size policy to expand and fill available space (responsive)
            self._chart_view.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            # Ensure a taller chart area even when the window size remains fixed
            self._chart_view.setMinimumHeight(self._chart_min_height)
            # Remove fixed minimum size to allow responsiveness
            # Chart will adapt to available space in the layout

            # Add with stretch factor to take up maximum space
            self.ui.chartLayout.addWidget(self._chart_view, stretch=1)

            # Apply responsive font sizing after widget is shown
            self._apply_responsive_chart_styling(chart)

            # Hide placeholder text now that a chart is visible
            self.ui.label_chartplaceholder.setVisible(False)

            # Ensure existing X axes stay visible (avoid overriding custom axes)
            # Note: createDefaultAxes() can replace QDateTimeAxis/QBarCategoryAxis
            # and remove the intended label formatting for time-series charts.
            for axis in chart.axes(Qt.Orientation.Horizontal):
                axis.setVisible(True)

            self.logger.info("Chart generation completed successfully")
            self._set_chart_status("Ready", is_error=False)
        except Exception:
            self.logger.error("Chart rendering failed", exc_info=True)
            self._set_chart_status("Chart generation failed", is_error=True)
            QMessageBox.critical(
                self,
                "Unable to Generate Chart",
                "The chart could not be created. Technical details are saved in logs.",
            )
        finally:
            # Always restore cursor and clear cache
            QApplication.restoreOverrideCursor()
            self._series_cache = None
            self._pending_chart_context = None

    def _on_chart_worker_error(self, error_message: str) -> None:
        """Handle background worker errors (UI thread)."""
        QApplication.restoreOverrideCursor()
        self._set_chart_status(f"Error: {error_message}", is_error=True)
        QMessageBox.critical(
            self,
            "Chart Data Error",
            "Failed to load chart data. Check logs for details.",
        )

    def _clear_chart_worker(self) -> None:
        """Cleanup worker and thread after completion to avoid leaks."""
        if self._chart_worker:
            self._chart_worker.deleteLater()
        if self._chart_thread:
            self._chart_thread.deleteLater()
        self._chart_worker = None
        self._chart_thread = None

    def stop_background_tasks(self) -> None:
        """Stop any active background chart work (SHUTDOWN SAFETY).

        This is called by the main window during app exit to ensure
        background threads don't keep running after UI teardown.
        """
        if self._chart_thread and self._chart_thread.isRunning():
            # Best-effort shutdown; chart worker is short-lived.
            self.logger.info("Stopping analytics background worker on exit")
            self._chart_thread.quit()
            stopped = self._chart_thread.wait(5000)
            if not stopped and self._chart_thread.isRunning():
                self.logger.warning(
                    "Analytics worker did not stop in time; leaving graceful shutdown path"
                )

    def _set_chart_status(self, message: str, is_error: bool) -> None:
        """Update status label styling based on message severity.

        Args:
            message: Text to display below the chart controls.
            is_error: When True, use error styling for visibility.
        """
        if not hasattr(self, "_status_label"):
            return
        color = PALETTE["danger"] if is_error else PALETTE["muted"]
        weight = "font-weight: bold;" if is_error else ""
        self._status_label.setText(message)
        self._status_label.setStyleSheet("")

    def _get_series_data(
        self,
        source_name: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[Tuple[date, float]]:
        """Get series data from cache or Excel manager.

        Cache strategy:
        - Key: source name
        - TTL: Single chart generation
        - Invalidation: Cleared after rendering completes
        """
        if self._series_cache and source_name in self._series_cache:
            return self._series_cache[source_name]

        # Fallback to Excel manager (Meter Readings Excel)
        return self._get_series_data(
            source_name=source_name,
            start_date=start_date,
            end_date=end_date,
        )

    def _generate_chart_impl(self) -> None:
        """Internal chart generation (called with wait cursor active)."""
        # Ensure the Meter Readings path is configured before rendering
        if not self._ensure_meter_readings_path():
            return
        if not HAS_QTCHARTS:
            # Leave the placeholder label visible; QtCharts not available
            self.ui.label_chartplaceholder.setText(
                "QtCharts not available. Install PySide6-Addons to enable charts."
            )
            self.ui.label_chartplaceholder.setAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            )
            return

        raw_source = self.ui.water_source_options.currentText().strip()
        if not raw_source:
            QMessageBox.warning(self, "Missing Source", "Please select a water source.")
            return

        selected_sources = self._get_selected_sources(raw_source)
        if not selected_sources:
            QMessageBox.warning(
                self,
                "Missing Source",
                "Please select at least one water source.",
            )
            return

        start_date, end_date = self._get_selected_date_range()
        chart_type = self.ui.charts_options.currentText().strip()
        title = self._build_chart_title(raw_source, start_date, end_date, chart_type)
        y_label = self._build_y_axis_label(raw_source)

        # Render chart by selected type
        is_multi = len(selected_sources) > 1
        if chart_type == "Stacked Bar" and not is_multi:
            QMessageBox.information(
                self,
                "Not Supported",
                "Stacked charts require multiple sources. Select 'All Sources' or add more.",
            )
            return

        if is_multi:
            chart = self._build_multi_series_chart(
                selected_sources=selected_sources,
                start_date=start_date,
                end_date=end_date,
                chart_type=chart_type,
                title=title,
                raw_source_name=raw_source,  # Pass for title correction
            )
        else:
            source_name = selected_sources[0]
            series_data = self._get_series_data(
                source_name=source_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not series_data:
                QMessageBox.information(
                    self,
                    "No Data",
                    "No data available for the selected source/date range.",
                )
                return

            # Get actual date range from data for accurate title
            actual_start = min(d for d, v in series_data)
            actual_end = max(d for d, v in series_data)
            actual_range = (actual_start, actual_end)

            # Rebuild title with actual data range
            title = self._build_chart_title(
                raw_source,
                start_date,
                end_date,
                chart_type,
                actual_data_range=actual_range,
            )

            chart = self._build_single_series_chart(
                series_data=series_data,
                source_name=source_name,
                chart_type=chart_type,
                title=title,
                y_label=y_label,
            )

        # Replace any existing chart view
        if self._chart_view is not None:
            self.ui.chartLayout.removeWidget(self._chart_view)
            self._chart_view.deleteLater()
            self._chart_view = None

        self._chart_view = QChartView(chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set size policy to expand and fill available space (responsive)
        self._chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Remove fixed minimum size to allow responsiveness
        # Chart will adapt to available space in the layout

        # Add with stretch factor to take up maximum space
        self.ui.chartLayout.addWidget(self._chart_view, stretch=1)

        # Apply responsive font sizing after widget is shown
        self._apply_responsive_chart_styling(chart)

        # Hide placeholder text now that a chart is visible
        self.ui.label_chartplaceholder.setVisible(False)

    def _get_selected_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """Parse year/month combos into optional date range.

        Returns:
            (start_date, end_date) where values are datetime.date or None.
        """
        start_year = self.ui.year_from.currentText().strip()
        start_month = self.ui.month_from.currentText().strip()
        end_year = self.ui.year_to.currentText().strip()
        end_month = self.ui.month_to.currentText().strip()

        start_date = None
        end_date = None

        if start_year:
            month = int(start_month) if start_month else 1
            start_date = date(int(start_year), month, 1)

        if end_year:
            month = int(end_month) if end_month else 12
            end_date = date(int(end_year), month, 1)

        return start_date, end_date

    def _load_chart_type_options(self) -> None:
        """Populate chart type dropdown with supported time-series options."""
        chart_types = [
            "Line Chart",
            "Spline Chart",
            "Scatter Chart",
            "Bar Chart",
            "Stacked Bar",
        ]
        self.ui.charts_options.clear()
        self.ui.charts_options.addItems(chart_types)

    def _get_selected_sources(self, raw_source: str) -> List[str]:
        """Resolve selected sources from combo input.

        Supports:
        - "All Sources" for full list
        - Custom Selection label for multi-select dialog
        - Single source for standard charts
        """
        if raw_source == "All Sources":
            return self._excel_manager.list_meter_readings_sources()

        if raw_source.startswith("Custom Selection"):
            return self._selected_sources

        return [raw_source]

    def _on_save_chart(self) -> None:
        """Save the current chart as an image.

        Uses the chart view grab to export a PNG suitable for reports.
        """
        if self._chart_view is None:
            QMessageBox.information(self, "No Chart", "Generate a chart first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chart",
            "analytics_chart.png",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;PDF Document (*.pdf);;SVG Vector (*.svg);;All Files (*.*)",
        )
        if not path:
            return

        suffix = Path(path).suffix.lower()
        if suffix == ".pdf":
            if not self._export_chart_to_pdf(path):
                QMessageBox.warning(self, "Save Failed", "Unable to save chart as PDF.")
                return
        elif suffix == ".svg":
            if not self._export_chart_to_svg(path):
                QMessageBox.warning(self, "Save Failed", "Unable to save chart as SVG.")
                return
        else:
            # Default image export (PNG/JPEG)
            pixmap = self._chart_view.grab()
            if not pixmap.save(path):
                QMessageBox.warning(self, "Save Failed", "Unable to save chart image.")
                return

        QMessageBox.information(self, "Saved", f"Chart saved to:\n{path}")

    def _export_chart_to_pdf(self, path: str) -> bool:
        """Export chart to PDF for report-ready output.

        Uses QPdfWriter and QPainter to render the chart view.
        """
        try:
            size = self._chart_view.size()
            pdf = QPdfWriter(path)
            pdf.setPageSize(
                QPageSize(QSizeF(size.width(), size.height()), QPageSize.Unit.Point)
            )
            pdf.setResolution(300)

            painter = QPainter(pdf)
            self._chart_view.render(painter)
            painter.end()
            return True
        except Exception:
            return False

    def _export_chart_to_svg(self, path: str) -> bool:
        """Export chart to SVG (vector) for report usage.

        Returns False if QtSvg is unavailable.
        """
        if not HAS_QTSVG or QSvgGenerator is None:
            QMessageBox.information(
                self,
                "SVG Not Available",
                "QtSvg is not available. Install PySide6-Addons to enable SVG export.",
            )
            return False

        try:
            size = self._chart_view.size()
            generator = QSvgGenerator()
            generator.setFileName(path)
            generator.setSize(size)
            generator.setViewBox(QRect(0, 0, size.width(), size.height()))

            painter = QPainter(generator)
            self._chart_view.render(painter)
            painter.end()
            return True
        except Exception:
            return False

    def _build_chart_title(
        self,
        source_name: str,
        start_date: Optional[date],
        end_date: Optional[date],
        chart_type: str,
        actual_data_range: Optional[Tuple[date, date]] = None,
    ) -> str:
        """Build a report-quality chart title based on selection.

        Auto-adjusts to actual data range for better UX (avoids misleading titles
        when user selects 2006-2025 but data only exists for 2010-2025).

        Args:
            source_name: Source column name
            start_date: User-requested start date
            end_date: User-requested end date
            chart_type: Chart type string
            actual_data_range: Actual (min, max) dates from loaded data (overrides user selection)

        Returns:
            Formatted title string
        """
        # Use actual data range if provided (more accurate)
        if actual_data_range:
            actual_start, actual_end = actual_data_range
            date_range = (
                f"{actual_start.strftime('%b %Y')} - {actual_end.strftime('%b %Y')}"
            )
        elif start_date or end_date:
            start_text = start_date.strftime("%b %Y") if start_date else "Start"
            end_text = end_date.strftime("%b %Y") if end_date else "Latest"
            date_range = f"{start_text} - {end_text}"
        else:
            date_range = "All Dates"

        return f"{source_name} ({chart_type}) | {date_range}"

    def _build_y_axis_label(self, source_name: str) -> str:
        """Build Y-axis label from Excel unit row or fallback to keyword inference.

        First tries to get the unit from Excel row 4 (units row).
        Falls back to keyword-based inference if unit not found.
        """
        # Try to get unit from Excel row 4
        unit = self._excel_manager.get_source_unit(source_name)
        if unit and unit not in ["nan", "None", ""]:
            return unit

        # Fallback to keyword-based inference
        name = source_name.lower()
        if "ton" in name or "tonne" in name:
            return "Tonnes"
        if "ml" in name or "mega" in name:
            return "ML"
        if "%" in name or "percent" in name or "recycl" in name:
            return "Percentage (%)"
        if "moisture" in name or "wet" in name:
            return "Moisture (%)"
        return "Value"

    def _build_multi_series_chart(
        self,
        selected_sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        chart_type: str,
        title: str,
        raw_source_name: str = "Custom Selection",
    ) -> QChart:
        """Build a multi-series chart for comparison scenarios.

        Auto-adjusts title to actual data range for better UX.
        """
        # Limit series count to keep chart readable in reports
        sources = selected_sources[:12]

        if chart_type == "Stacked Bar":
            chart = self._build_stacked_bar_chart(sources, start_date, end_date, title)
        elif chart_type == "Bar Chart":
            # Bar Chart with multiple sources falls back to Line Chart for time-series compatibility
            chart = self._build_multi_line_chart(sources, start_date, end_date, title)
            # Update chart type to reflect what's actually shown
            chart_type = "Line Chart"
        elif chart_type == "Scatter Chart":
            chart = self._build_multi_scatter_chart(
                sources, start_date, end_date, title
            )
        elif chart_type == "Spline Chart":
            chart = self._build_multi_spline_chart(sources, start_date, end_date, title)
        else:
            chart = self._build_multi_line_chart(sources, start_date, end_date, title)

        # Extract actual date range from chart's X axis and update title
        actual_range = self._extract_actual_date_range_from_chart(chart)

        # For Stacked Bar and other category-based charts, use start/end dates if actual_range not available
        if not actual_range and (start_date or end_date):
            actual_range = (start_date, end_date) if start_date and end_date else None

        # Always update title for multi-select to show actual source names
        if "Custom Selection" in raw_source_name or actual_range:
            # Show actual source names instead of "Custom Selection (2)"
            if "Custom Selection" in raw_source_name:
                source_list = ", ".join(sources[:3])  # Show first 3 sources
                if len(sources) > 3:
                    source_list += f" + {len(sources) - 3} more"
                display_name = source_list
            else:
                display_name = raw_source_name

            updated_title = self._build_chart_title(
                display_name,
                start_date,
                end_date,
                chart_type,
                actual_data_range=actual_range,
            )
            chart.setTitle(updated_title)

        return chart

    def _extract_actual_date_range_from_chart(
        self, chart: QChart
    ) -> Optional[Tuple[date, date]]:
        """Extract actual min/max dates from chart's X axis (for title correction).

        Converts QDate objects to Python date objects for compatibility with strftime().

        Returns:
            (min_date, max_date) as Python date objects, or None if not a date-based chart
        """
        try:
            for axis in chart.axes(Qt.Orientation.Horizontal):
                if isinstance(axis, QDateTimeAxis):
                    min_dt = axis.min()  # Returns QDateTime
                    max_dt = axis.max()  # Returns QDateTime
                    # Convert QDate to Python date objects for strftime compatibility
                    min_qdate = min_dt.date()  # QDate object
                    max_qdate = max_dt.date()  # QDate object
                    min_py_date = date(
                        min_qdate.year(), min_qdate.month(), min_qdate.day()
                    )
                    max_py_date = date(
                        max_qdate.year(), max_qdate.month(), max_qdate.day()
                    )
                    return (min_py_date, max_py_date)
        except Exception:
            pass
        return None

    def _build_single_series_chart(
        self,
        series_data: List[Tuple[date, float]],
        source_name: str,
        chart_type: str,
        title: str,
        y_label: str,
    ) -> QChart:
        """Build a single-series chart based on chart type."""
        if chart_type == "Bar Chart":
            return self._build_bar_chart(series_data, source_name, title, y_label)
        if chart_type == "Spline Chart":
            return self._build_spline_chart(series_data, source_name, title, y_label)
        if chart_type == "Scatter Chart":
            return self._build_scatter_chart(series_data, source_name, title, y_label)
        return self._build_line_chart(series_data, source_name, title, y_label)

    def _build_multi_line_chart(
        self,
        sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        title: str,
    ) -> QChart:
        """Build a multi-series line chart with shared Date axis."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QDateTimeAxis()
        x_axis.setFormat("MMM yyyy")
        x_axis.setTitleText("Date")
        # Increase label font size for better readability
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)

        y_axis = QValueAxis()
        # Get unit from first source (all sources assumed to have same unit for multi-series)
        unit_label = self._build_y_axis_label(sources[0]) if sources else "Value"
        y_axis.setTitleText(unit_label)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)

        min_dt: Optional[QDateTime] = None
        max_dt: Optional[QDateTime] = None
        min_value: Optional[float] = None
        max_value: Optional[float] = None

        for source_name in sources:
            series_data = self._get_series_data(
                source_name=source_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not series_data:
                continue

            series = QLineSeries()
            series.setName(source_name)

            for d, v in series_data:
                dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
                series.append(dt.toMSecsSinceEpoch(), v)
                if min_dt is None or dt < min_dt:
                    min_dt = dt
                if max_dt is None or dt > max_dt:
                    max_dt = dt
                # Track Y-axis data range for auto-scaling
                if min_value is None or v < min_value:
                    min_value = v
                if max_value is None or v > max_value:
                    max_value = v

            chart.addSeries(series)
            series.attachAxis(x_axis)
            series.attachAxis(y_axis)

        if min_dt and max_dt:
            x_axis.setRange(min_dt, max_dt)
        
        # Auto-scale Y-axis based on actual data range
        if min_value is not None and max_value is not None:
            self._auto_scale_y_axis(y_axis, min_value, max_value)

        # Apply styling to axes directly instead of using _style_axes
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))
        self._enable_legend_filtering(chart)
        return chart

    def _build_multi_spline_chart(
        self,
        sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        title: str,
    ) -> QChart:
        """Build multi-series spline chart for smoother trends."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QDateTimeAxis()
        x_axis.setFormat("MMM yyyy")
        x_axis.setTitleText("Date")
        # Increase label font size for better readability
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)

        y_axis = QValueAxis()
        # Get unit from first source (all sources assumed to have same unit for multi-series)
        unit_label = self._build_y_axis_label(sources[0]) if sources else "Value"
        y_axis.setTitleText(unit_label)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)

        min_dt: Optional[QDateTime] = None
        max_dt: Optional[QDateTime] = None
        min_value: Optional[float] = None
        max_value: Optional[float] = None

        for source_name in sources:
            series_data = self._get_series_data(
                source_name=source_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not series_data:
                continue

            series = QSplineSeries()
            series.setName(source_name)

            for d, v in series_data:
                dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
                series.append(dt.toMSecsSinceEpoch(), v)
                if min_dt is None or dt < min_dt:
                    min_dt = dt
                if max_dt is None or dt > max_dt:
                    max_dt = dt
                # Track Y-axis data range for auto-scaling
                if min_value is None or v < min_value:
                    min_value = v
                if max_value is None or v > max_value:
                    max_value = v

            chart.addSeries(series)
            series.attachAxis(x_axis)
            series.attachAxis(y_axis)

        if min_dt and max_dt:
            x_axis.setRange(min_dt, max_dt)

        # Apply styling to axes directly instead of using _style_axes
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))
        self._enable_legend_filtering(chart)
        return chart

    def _build_multi_scatter_chart(
        self,
        sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        title: str,
    ) -> QChart:
        """Build multi-series scatter chart for comparisons."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QDateTimeAxis()
        x_axis.setFormat("MMM yyyy")
        x_axis.setTitleText("Date")
        # Increase label font size for better readability
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)

        y_axis = QValueAxis()
        # Get unit from first source (all sources assumed to have same unit for multi-series)
        unit_label = self._build_y_axis_label(sources[0]) if sources else "Value"
        y_axis.setTitleText(unit_label)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)

        min_dt: Optional[QDateTime] = None
        max_dt: Optional[QDateTime] = None
        min_value: Optional[float] = None
        max_value: Optional[float] = None

        for source_name in sources:
            series_data = self._get_series_data(
                source_name=source_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not series_data:
                continue

            series = QScatterSeries()
            series.setName(source_name)
            series.setMarkerSize(6.0)

            for d, v in series_data:
                dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
                series.append(dt.toMSecsSinceEpoch(), v)
                if min_dt is None or dt < min_dt:
                    min_dt = dt
                if max_dt is None or dt > max_dt:
                    max_dt = dt
                # Track Y-axis data range for auto-scaling
                if min_value is None or v < min_value:
                    min_value = v
                if max_value is None or v > max_value:
                    max_value = v

            chart.addSeries(series)
            series.attachAxis(x_axis)
            series.attachAxis(y_axis)

        if min_dt and max_dt:
            x_axis.setRange(min_dt, max_dt)
        
        # Auto-scale Y-axis based on actual data range
        if min_value is not None and max_value is not None:
            self._auto_scale_y_axis(y_axis, min_value, max_value)

        # Apply styling to axes directly instead of using _style_axes
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))
        self._enable_legend_filtering(chart)
        return chart

    def _build_stacked_bar_chart(
        self,
        sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        title: str,
    ) -> QChart:
        """Build stacked bar chart across sources by month."""
        aligned = self._build_aligned_series(sources, start_date, end_date)
        if not aligned:
            raise ValueError("No aligned data available for stacked bar chart")

        # Extract categories from aligned dates
        categories = [dt.toString("MMM yyyy") for dt in aligned[0][1].keys()]

        stacked_series = QStackedBarSeries()
        for source_name, series_map in aligned:
            bar_set = QBarSet(source_name)
            for dt in aligned[0][1].keys():
                bar_set.append(series_map.get(dt, 0.0))
            stacked_series.append(bar_set)

        chart = QChart()
        chart.addSeries(stacked_series)
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QBarCategoryAxis()

        # Handle label sampling for many categories
        display_categories = categories.copy()
        if len(categories) > 24:
            # Show only every 6th label when there are too many (avoids overcrowding)
            # For monthly data, this shows every 6 months
            for i in range(len(display_categories)):
                if i % 6 != 0:  # Keep every 6th label, hide others
                    display_categories[i] = ""

        x_axis.append(display_categories)
        x_axis.setTitleText("Date")
        # Rotate labels for better readability when many categories
        if len(categories) > 24:
            x_axis.setLabelsAngle(-45)

        # Apply styling to x-axis labels
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))

        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        stacked_series.attachAxis(x_axis)

        y_axis = QValueAxis()
        y_axis.setTitleText("Value")
        # Apply styling to y-axis labels
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))

        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        stacked_series.attachAxis(y_axis)

        # Add bottom margin to accommodate rotated labels
        chart.margins().setBottom(80)
        chart.margins().setLeft(80)

        # Don't call _style_axes for bar charts since we handle styling here
        self._enable_legend_filtering(chart)
        return chart

    def _build_aligned_series(
        self,
        sources: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[Tuple[str, Dict[QDateTime, float]]]:
        """Align series by date for stacked charts.

        Returns list of (source_name, {QDateTime: value}) ordered by date.
        """
        aligned: List[Tuple[str, Dict[QDateTime, float]]] = []
        all_dates: List[QDateTime] = []

        for source_name in sources:
            series_data = self._get_series_data(
                source_name=source_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not series_data:
                continue

            series_map: Dict[QDateTime, float] = {}
            for d, v in series_data:
                dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
                series_map[dt] = float(v)
                all_dates.append(dt)
            aligned.append((source_name, series_map))

        if not aligned:
            return []

        # Normalize date keys across all sources
        unique_dates = sorted(set(all_dates))
        normalized: List[Tuple[str, Dict[QDateTime, float]]] = []
        for source_name, series_map in aligned:
            normalized_map = {dt: series_map.get(dt, 0.0) for dt in unique_dates}
            normalized.append((source_name, normalized_map))

        return normalized

    def _build_spline_chart(
        self,
        series_data: List[Tuple[date, float]],
        source_name: str,
        title: str,
        y_label: str,
    ) -> QChart:
        """Build a single-series spline chart (smoothed line)."""
        series = QSplineSeries()
        series.setName(source_name)

        min_dt: Optional[QDateTime] = None
        max_dt: Optional[QDateTime] = None

        for d, v in series_data:
            dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
            series.append(dt.toMSecsSinceEpoch(), v)
            if min_dt is None or dt < min_dt:
                min_dt = dt
            if max_dt is None or dt > max_dt:
                max_dt = dt

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QDateTimeAxis()
        x_axis.setFormat("MMM yyyy")
        x_axis.setTitleText("Date")
        # Increase label font size for better readability
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        if min_dt and max_dt:
            x_axis.setRange(min_dt, max_dt)
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(x_axis)

        y_axis = QValueAxis()
        y_axis.setTitleText(y_label)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(y_axis)

        # Auto-scale Y-axis based on actual data range
        if len(series_data) > 0:
            values = [v for _, v in series_data]
            min_val = min(values)
            max_val = max(values)
            self._auto_scale_y_axis(y_axis, min_val, max_val)

        # Apply styling to axes directly instead of using _style_axes
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))
        self._enable_legend_filtering(chart)
        return chart

    def _build_scatter_chart(
        self,
        series_data: List[Tuple[date, float]],
        source_name: str,
        title: str,
        y_label: str,
    ) -> QChart:
        """Build a single-series scatter chart."""
        series = QScatterSeries()
        series.setName(source_name)
        series.setMarkerSize(6.0)

        min_dt: Optional[QDateTime] = None
        max_dt: Optional[QDateTime] = None

        for d, v in series_data:
            dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
            series.append(dt.toMSecsSinceEpoch(), v)
            if min_dt is None or dt < min_dt:
                min_dt = dt
            if max_dt is None or dt > max_dt:
                max_dt = dt

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QDateTimeAxis()
        x_axis.setFormat("MMM yyyy")
        x_axis.setTitleText("Date")
        # Increase label font size for better readability
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        if min_dt and max_dt:
            x_axis.setRange(min_dt, max_dt)
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(x_axis)

        y_axis = QValueAxis()
        y_axis.setTitleText(y_label)
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(y_axis)

        # Auto-scale Y-axis based on actual data range
        if len(series_data) > 0:
            values = [v for _, v in series_data]
            min_val = min(values)
            max_val = max(values)
            self._auto_scale_y_axis(y_axis, min_val, max_val)

        # Apply styling to axes directly instead of using _style_axes
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))
        self._enable_legend_filtering(chart)
        return chart

    def _build_line_chart(
        self,
        series_data: List[Tuple[date, float]],
        source_name: str,
        title: str,
        y_label: str,
    ) -> QChart:
        """Build a line chart with DateTime X axis."""
        series = QLineSeries()
        series.setName(source_name)

        # Track min/max for axis range
        min_dt: Optional[QDateTime] = None
        max_dt: Optional[QDateTime] = None

        for d, v in series_data:
            dt = QDateTime(QDate(d.year, d.month, d.day), QTime(0, 0))
            series.append(dt.toMSecsSinceEpoch(), v)
            if min_dt is None or dt < min_dt:
                min_dt = dt
            if max_dt is None or dt > max_dt:
                max_dt = dt

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QDateTimeAxis()
        x_axis.setFormat("MMM yyyy")
        x_axis.setTitleText("Date")
        # Increase label font size for better readability
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))
        if min_dt and max_dt:
            x_axis.setRange(min_dt, max_dt)
        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(x_axis)

        y_axis = QValueAxis()
        y_axis.setTitleText(y_label)
        # Apply styling to y-axis labels
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))
        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(y_axis)

        # Auto-scale Y-axis based on actual data range (extract from series)
        if len(series_data) > 0:
            values = [v for _, v in series_data]
            min_val = min(values)
            max_val = max(values)
            self._auto_scale_y_axis(y_axis, min_val, max_val)

        # Don't call _style_axes for line charts since we handle styling here
        self._enable_legend_filtering(chart)
        return chart

    def _build_bar_chart(
        self,
        series_data: List[Tuple[date, float]],
        source_name: str,
        title: str,
        y_label: str,
    ) -> QChart:
        """Build a bar chart with month categories on X axis.

        Auto-rotates labels when data points > 24 to prevent overlap.
        Optimizes for readability with smart label sampling for large datasets.
        """
        bar_set = QBarSet(source_name)
        categories: List[str] = []

        for d, v in series_data:
            categories.append(d.strftime("%b %Y"))
            bar_set.append(v)

        bar_series = QBarSeries()
        bar_series.append(bar_set)

        chart = QChart()
        chart.addSeries(bar_series)
        chart.setTitle(title)
        chart.legend().setVisible(True)
        self._apply_chart_theme(chart)

        x_axis = QBarCategoryAxis()

        # Smart label sampling: show every Nth label if too many categories
        # This prevents label crowding while keeping axis readable
        if len(categories) > 36:
            # For 36+ categories: show every 3rd label
            sample_interval = 3
            display_categories = [
                "" if i % sample_interval != 0 else cat
                for i, cat in enumerate(categories)
            ]
            x_axis.append(display_categories)
        elif len(categories) > 24:
            # For 24-36 categories: show every 2nd label
            sample_interval = 2
            display_categories = [
                "" if i % sample_interval != 0 else cat
                for i, cat in enumerate(categories)
            ]
            x_axis.append(display_categories)
        else:
            # Show all labels for smaller datasets
            x_axis.append(categories)

        x_axis.setTitleText("Date")
        # Always rotate labels for better readability with bars
        x_axis.setLabelsAngle(-45)
        # Increase label size for visibility
        x_axis_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        x_axis.setLabelsFont(x_axis_font)
        x_axis.setLabelsColor(QColor(PALETTE["text"]))

        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        bar_series.attachAxis(x_axis)

        y_axis = QValueAxis()
        y_axis.setTitleText(y_label)
        # Apply styling to y-axis labels
        y_axis_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        y_axis.setLabelsFont(y_axis_font)
        y_axis.setLabelsColor(QColor(PALETTE["text"]))
        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(QColor(PALETTE["border"]))

        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        bar_series.attachAxis(y_axis)

        # Auto-scale Y-axis based on actual data range from bar set
        if len(series_data) > 0:
            values = [v for _, v in series_data]
            min_val = min(values)
            max_val = max(values)
            self._auto_scale_y_axis(y_axis, min_val, max_val)

        # Add bottom margin to accommodate rotated labels
        chart.margins().setBottom(80)
        chart.margins().setLeft(80)

        # Don't call _style_axes for bar charts since we handle styling here
        self._enable_legend_filtering(chart)
        return chart

    @staticmethod
    def _apply_chart_theme(chart: QChart) -> None:
        """Apply a report-ready chart theme (colors, grid, fonts).

        Style goals:
        - Clean white background for exports
        - Subtle plot area contrast
        - Consistent fonts for reporting
        """
        chart.setBackgroundVisible(True)
        chart.setBackgroundBrush(QColor(PALETTE["surface"]))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setPlotAreaBackgroundBrush(QColor(PALETTE["surface_alt"]))

        title_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        chart.setTitleFont(title_font)
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor(PALETTE["text"]))

    @staticmethod
    def _style_axes(
        x_axis: QDateTimeAxis | QCategoryAxis | QBarCategoryAxis,
        y_axis: QValueAxis,
    ) -> None:
        """Apply consistent axis styling for readability in reports."""
        axis_font = QFont(
            "Segoe UI", 11
        )  # Increased from 9 to 11 for better readability
        label_color = QColor(PALETTE["text"])
        grid_color = QColor(PALETTE["border"])

        x_axis.setLabelsFont(axis_font)
        x_axis.setLabelsColor(label_color)
        y_axis.setLabelsFont(axis_font)
        y_axis.setLabelsColor(label_color)

        y_axis.setGridLineVisible(True)
        y_axis.setGridLineColor(grid_color)

    @staticmethod
    def _auto_scale_y_axis(y_axis: QValueAxis, min_value: float, max_value: float) -> None:
        """Auto-scale Y-axis with 10% padding to fit all data nicely.
        
        Args:
            y_axis: The Y-axis to configure.
            min_value: Minimum data value.
            max_value: Maximum data value.
        """
        if min_value == max_value:
            # Avoid division by zero; just add some padding
            min_value -= 1
            max_value += 1
        
        # Add 10% padding above and below for visual breathing room
        value_range = max_value - min_value
        padding = value_range * 0.1
        
        y_axis.setRange(min_value - padding, max_value + padding)

    @staticmethod
    def _enable_legend_filtering(chart: QChart) -> None:
        """Enable click-to-toggle series visibility via legend.

        This is especially useful for comparison charts (boreholes, features)
        where users want to isolate a subset without regenerating the chart.
        """
        try:
            for marker in chart.legend().markers():
                series = marker.series()
                if series is None:
                    continue
                marker.clicked.connect(
                    lambda checked=False, m=marker, s=series: AnalyticsPage._toggle_series(
                        m, s
                    )
                )
        except Exception:
            # Some chart types may not support markers; treat as best-effort
            return

    @staticmethod
    def _toggle_series(marker, series) -> None:
        """Toggle a series and dim legend label when hidden."""
        visible = not series.isVisible()
        series.setVisible(visible)

        # Keep legend entry visible but visually dim when hidden
        marker.setLabelBrush(
            QColor(PALETTE["text"]) if visible else QColor(PALETTE["muted_light"])
        )

    def _apply_responsive_chart_styling(self, chart: QChart) -> None:
        """Apply responsive font sizing based on available chart size.

        This method adjusts font sizes dynamically to ensure x-axis labels
        remain readable on different screen sizes while maintaining responsiveness.
        """
        # Schedule the styling to run after the widget is properly sized
        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, lambda: self._adjust_font_sizes(chart))

    def _adjust_font_sizes(self, chart: QChart) -> None:
        """Dynamically adjust font sizes based on chart dimensions."""
        if not self._chart_view or not chart:
            return

        # Get current chart size
        chart_size = self._chart_view.size()
        chart_width = chart_size.width()

        # Calculate appropriate font sizes based on chart dimensions
        # Base font sizes for different screen sizes
        if chart_width < 800:  # Small screens (laptops)
            x_font_size = 8
            title_font_size = 10
        elif chart_width < 1200:  # Medium screens
            x_font_size = 9
            title_font_size = 11
        else:  # Large screens (27"+)
            x_font_size = 10
            title_font_size = 12

        # Apply font sizes to all axes
        for axis in chart.axes():
            if hasattr(axis, "labelsFont"):
                font = QFont("Segoe UI", x_font_size, QFont.Weight.Bold)
                axis.setLabelsFont(font)
                axis.setLabelsColor(QColor(PALETTE["text"]))

        # Adjust title font if needed
        if chart.title():
            title_font = QFont("Segoe UI", title_font_size, QFont.Weight.Bold)
            chart.setTitleFont(title_font)


