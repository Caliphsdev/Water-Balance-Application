# PySide6 Modules Reference Guide

**Status:** Ready for Phase 5+ Implementation  
**Last Updated:** February 2, 2026  
**Purpose:** Guide for leveraging PySide6 modules to enhance Water Balance Dashboard

---

## 📦 Current Module Usage

### ✅ **Core Modules (Currently Active)**

| Module | Current Usage | Files |
|--------|---------------|-------|
| **QtCore** | Signals/slots, timers, animations, enums | `main.py`, `main_window.py`, all dashboards |
| **QtWidgets** | All UI components (QWidget, QMainWindow, QLabel, etc.) | Entire `ui/` directory |
| **QtGui** | Graphics (QPixmap, QFont, QPainter) | `splash_screen.py`, custom widgets |

**Evidence:**
```python
# src/main.py
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# src/ui/main_window.py
from PySide6.QtCore import Slot, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QFont

# src/ui/components/splash_screen.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
```

---

## 🎯 Recommended Modules for Future Phases

### **Priority 1: QtCharts (Phase 5 - Analytics Dashboard)**

**Purpose:** Native Qt charting library for professional data visualization

**Benefits:**
- ✅ Seamless PySide6 integration (no matplotlib dependency)
- ✅ Native styling matches application theme
- ✅ Better performance for real-time updates
- ✅ Interactive charts (tooltips, zoom, pan)
- ✅ Multiple chart types: Line, Bar, Pie, Area, Scatter

**Use Cases:**
- **Analytics Dashboard**: KPI trend charts (storage levels, inflows, outflows)
- **Monitoring Dashboard**: Real-time data visualization
- **Calculation Dashboard**: Balance error trends over time

**Implementation Example:**
```python
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PySide6.QtCore import QDateTime

class AnalyticsPage(QWidget):
    def _create_storage_trend_chart(self, data: dict):
        """Create line chart showing storage level trends (ANALYTICS CHART).
        
        Args:
            data: Dict with 'dates' (list of datetime) and 'levels' (list of float)
        
        Returns:
            QChartView widget ready to add to layout
        """
        # Create series
        series = QLineSeries()
        series.setName("Storage Level (%)")
        
        for date, level in zip(data['dates'], data['levels']):
            timestamp = QDateTime(date).toMSecsSinceEpoch()
            series.append(timestamp, level)
        
        # Create chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Storage Level Trend (12 Months)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Add axes
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Level (%)")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view
```

**Migration from Matplotlib:**
```python
# BEFORE (matplotlib):
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
fig, ax = plt.subplots()
ax.plot(dates, levels)
canvas = FigureCanvasQTAgg(fig)

# AFTER (QtCharts):
chart = QChart()
series = QLineSeries()
# ... (see example above)
chart_view = QChartView(chart)
```

**Resources:**
- [QtCharts Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCharts/index.html)
- [Chart Types Gallery](https://doc.qt.io/qt-6/qtcharts-overview.html)

---

### **Priority 2: QtSvg + QtSvgWidgets (Phase 5 - Flow Diagram Enhancement)**

**Purpose:** Scalable vector graphics support for crisp, resolution-independent rendering

**Benefits:**
- ✅ Scalable graphics (zoom without pixelation)
- ✅ Smaller file sizes than PNG/JPG
- ✅ Easy styling via CSS-like attributes
- ✅ Perfect for flow diagram components (tanks, pipes, pumps)

**Use Cases:**
- **Flow Diagram Page**: Render facility icons, pipes, arrows
- **Dashboard Icons**: Scalable KPI card icons
- **Branding**: Company logo at any size

**Implementation Example:**
```python
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray

class FlowDiagramPage(QWidget):
    def _add_facility_icon(self, facility_type: str, x: int, y: int):
        """Add SVG facility icon to flow diagram (SCALABLE GRAPHICS).
        
        Args:
            facility_type: 'tank', 'pump', 'treatment_plant', etc.
            x, y: Position coordinates
        """
        # Load SVG from resources
        svg_widget = QSvgWidget(f":/icons/facilities/{facility_type}.svg")
        svg_widget.setGeometry(x, y, 80, 80)  # Scales cleanly to any size
        svg_widget.setParent(self)
        
        # Optional: Modify SVG color dynamically
        renderer = svg_widget.renderer()
        # Can update fill colors via SVG manipulation
```

**SVG Asset Structure:**
```
data/flow_diagram_assets/
├── facilities/
│   ├── storage_tank.svg
│   ├── pump.svg
│   ├── treatment_plant.svg
│   └── underground_shaft.svg
├── pipes/
│   ├── pipe_straight.svg
│   ├── pipe_corner.svg
│   └── arrow.svg
└── icons/
    ├── inflow.svg
    ├── outflow.svg
    └── recirculation.svg
```

**Resources:**
- [QtSvg Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtSvg/index.html)
- SVG Icon Libraries: [Heroicons](https://heroicons.com/), [Lucide](https://lucide.dev/)

---

### **Priority 3: QtPrintSupport (Phase 6 - Reporting)**

**Purpose:** Native PDF export and printing support

**Benefits:**
- ✅ Export dashboards to PDF (replace reportlab)
- ✅ Print preview dialogs
- ✅ Custom page layouts
- ✅ Embed charts and tables

**Use Cases:**
- **Dashboard Export**: Save current view as PDF report
- **Analytics Reports**: Monthly/quarterly KPI summaries
- **Flow Diagrams**: Print/export for documentation

**Implementation Example:**
```python
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PySide6.QtGui import QPainter

class DashboardPage(QWidget):
    def export_to_pdf(self, filename: str):
        """Export current dashboard view to PDF (REPORTING).
        
        Args:
            filename: Output PDF path (e.g., 'reports/dashboard_2026-02.pdf')
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageSize(QPrinter.A4)
        printer.setPageOrientation(QPrinter.Landscape)
        
        painter = QPainter(printer)
        self.render(painter)  # Render current widget to PDF
        painter.end()
        
        logger.info(f"Dashboard exported to {filename}")
    
    def show_print_dialog(self):
        """Show print preview dialog (USER ACTION)."""
        dialog = QPrintPreviewDialog()
        dialog.paintRequested.connect(self._print_preview)
        dialog.exec()
    
    def _print_preview(self, printer):
        """Render dashboard for print preview (INTERNAL)."""
        painter = QPainter(printer)
        self.render(painter)
        painter.end()
```

**Resources:**
- [QPrinter Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtPrintSupport/QPrinter.html)

---

### **Priority 4: QtSql (Phase 7 - Database Layer Upgrade)**

**Purpose:** Qt's SQL abstraction for better database integration

**Benefits:**
- ✅ Model/View pattern (QSqlTableModel, QSqlQueryModel)
- ✅ Automatic data binding to tables
- ✅ Built-in query caching
- ✅ Thread-safe connection management
- ✅ Easier debugging with query logging

**Use Cases:**
- **Storage Facilities Dashboard**: Direct table binding to QTableView
- **Database Manager**: Replace raw sqlite3 calls
- **Data Import**: Validate before insert using models

**Implementation Example:**
```python
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PySide6.QtWidgets import QTableView

class StorageFacilitiesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_database()
        self._setup_table_view()
    
    def _setup_database(self):
        """Initialize SQLite database connection (DB SETUP).
        
        Replaces raw sqlite3.connect() with Qt's connection pooling.
        """
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("data/water_balance.db")
        
        if not db.open():
            logger.error(f"Database connection failed: {db.lastError().text()}")
            return
        
        logger.info("Database connected via QtSql")
    
    def _setup_table_view(self):
        """Bind storage_facilities table to QTableView (DATA BINDING).
        
        Automatic CRUD operations, no manual SQL queries needed.
        """
        model = QSqlTableModel()
        model.setTable("storage_facilities")
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.select()
        
        # Set friendly column headers
        model.setHeaderData(0, Qt.Horizontal, "Code")
        model.setHeaderData(1, Qt.Horizontal, "Name")
        model.setHeaderData(2, Qt.Horizontal, "Capacity (m³)")
        
        # Bind to table view
        table_view = QTableView()
        table_view.setModel(model)
        table_view.resizeColumnsToContents()
```

**Migration from sqlite3:**
```python
# BEFORE (raw sqlite3):
import sqlite3
conn = sqlite3.connect("data/water_balance.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM storage_facilities")
rows = cursor.fetchall()

# AFTER (QtSql):
db = QSqlDatabase.addDatabase("QSQLITE")
db.setDatabaseName("data/water_balance.db")
db.open()

query = QSqlQuery("SELECT * FROM storage_facilities")
while query.next():
    code = query.value("code")
    name = query.value("name")
```

**Resources:**
- [QtSql Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtSql/index.html)
- [Model/View Programming](https://doc.qt.io/qt-6/model-view-programming.html)

---

## 🔧 Optional Modules (Consider Later)

### **QtNetwork (License Validation Enhancement)**

**Current:** Using `requests` library + `gspread` for Google Sheets API  
**Future:** Replace with QtNetwork for native Qt integration

**Benefits:**
- ✅ Async network requests (non-blocking)
- ✅ Better SSL/TLS support
- ✅ Integrated with Qt event loop

**Example:**
```python
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtCore import QUrl

class LicenseManager:
    def validate_license_async(self, license_key: str):
        """Validate license via Google Sheets API (ASYNC NETWORK).
        
        Non-blocking alternative to requests.get().
        """
        manager = QNetworkAccessManager()
        manager.finished.connect(self._on_license_response)
        
        url = QUrl(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}")
        request = QNetworkRequest(url)
        manager.get(request)
    
    def _on_license_response(self, reply):
        """Handle license validation response (CALLBACK)."""
        if reply.error():
            logger.error(f"License validation failed: {reply.errorString()}")
            return
        
        data = reply.readAll()
        # Parse JSON response
```

---

### **QtConcurrent (Background Calculations)**

**Current:** Using threading/async for heavy calculations  
**Future:** Replace with QtConcurrent for better Qt integration

**Benefits:**
- ✅ Thread pool management
- ✅ Progress reporting via signals
- ✅ Automatic cleanup

**Example:**
```python
from PySide6.QtConcurrent import QtConcurrent
from PySide6.QtCore import QFutureWatcher

class CalculationPage(QWidget):
    def calculate_balance_async(self, facility_code: str, month: int, year: int):
        """Run water balance calculation in background (NON-BLOCKING).
        
        Uses Qt thread pool instead of manual threading.
        """
        watcher = QFutureWatcher()
        watcher.finished.connect(self._on_calculation_complete)
        
        # Run in background thread
        future = QtConcurrent.run(
            self._heavy_calculation,
            facility_code,
            month,
            year
        )
        watcher.setFuture(future)
    
    def _heavy_calculation(self, facility_code, month, year):
        """Heavy calculation logic (RUNS IN WORKER THREAD)."""
        # ... water balance calculations ...
        return result
    
    def _on_calculation_complete(self):
        """Update UI with results (RUNS IN MAIN THREAD)."""
        watcher = self.sender()
        result = watcher.result()
        self._update_dashboard(result)
```

---

## 🚫 Modules NOT Needed

| Module | Reason | Alternative |
|--------|--------|-------------|
| **QtQml / QtQuick** | Using QtWidgets (classic), not QML (declarative) | Stick with QtWidgets |
| **QtQuickControls2** | QML-only controls | Use QtWidgets |
| **QtDesigner** | Design-time only (not runtime) | Compile .ui to .py |
| **QtDBus** | Linux IPC (Windows app) | N/A |
| **QtOpenGL / QtOpenGLWidgets** | No 3D graphics needed | Use QPainter for 2D |
| **QtHelp** | Qt Assistant help system | Use custom help pages |
| **QtUiTools** | Dynamic .ui loading | Compile .ui files to .py |
| **QtTest** | Qt-specific UI testing | Use pytest + pytest-qt |

---

## 📋 Implementation Roadmap

### **Phase 5: Analytics Dashboard (Q1 2026)**
- [ ] Add QtCharts dependency verification
- [ ] Replace matplotlib charts with QChartView
- [ ] Create chart templates (line, bar, pie)
- [ ] Implement interactive tooltips
- [ ] Add chart export to PNG/SVG

### **Phase 6: Flow Diagram Enhancement (Q2 2026)**
- [ ] Create SVG asset library (tanks, pumps, pipes)
- [ ] Refactor flow diagram renderer to use QSvgWidget
- [ ] Add zoom/pan with crisp SVG scaling
- [ ] Implement dynamic SVG color updates
- [ ] Export flow diagrams as vector PDF

### **Phase 7: Reporting Module (Q3 2026)**
- [ ] Implement QPrinter integration
- [ ] Add print preview dialogs
- [ ] Create PDF templates (dashboards, reports)
- [ ] Add batch export functionality
- [ ] Watermark and branding support

### **Phase 8: Database Layer Upgrade (Q4 2026)**
- [ ] Migrate to QSqlDatabase connections
- [ ] Replace manual queries with QSqlTableModel
- [ ] Implement model/view pattern for tables
- [ ] Add query result caching
- [ ] Performance comparison vs raw sqlite3

### **Future Considerations**
- [ ] Evaluate QtNetwork for license validation
- [ ] Test QtConcurrent for background calculations
- [ ] Consider QtMultimedia for sound alerts (optional)

---

## 📚 Resources

### **Official Documentation**
- [PySide6 API Reference](https://doc.qt.io/qtforpython-6/api.html)
- [Qt for Python Examples](https://doc.qt.io/qtforpython-6/examples/index.html)
- [Qt 6 Documentation](https://doc.qt.io/qt-6/)

### **Tutorials & Guides**
- [PySide6 Tutorial](https://www.pythonguis.com/pyside6-tutorial/)
- [Qt Charts Examples](https://doc.qt.io/qt-6/qtcharts-examples.html)
- [Model/View Programming Guide](https://doc.qt.io/qt-6/model-view-programming.html)

### **Community**
- [Qt Forum](https://forum.qt.io/)
- [Stack Overflow: PySide6](https://stackoverflow.com/questions/tagged/pyside6)

---

## ✅ Summary

**Current State:**
- ✅ QtCore, QtWidgets, QtGui (essential modules active)
- ✅ PySide6-Essentials installed
- ✅ PySide6-Addons installed (includes QtCharts, QtSvg, QtPrintSupport)

**Next Steps:**
1. **Phase 5**: Start using QtCharts for Analytics Dashboard
2. **Phase 6**: Enhance Flow Diagram with QtSvg
3. **Phase 7**: Add PDF export with QtPrintSupport
4. **Phase 8**: Migrate database layer to QtSql

**Key Takeaway:**  
You already have all the necessary modules installed via `PySide6-Addons`. The work is to **refactor existing code** to leverage these powerful Qt components for better performance, maintainability, and native Qt integration.

---

**Last Updated:** February 2, 2026  
**Next Review:** Phase 5 kickoff (post Phase 4 completion)
