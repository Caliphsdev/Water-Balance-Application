"""
Dashboard page controller for Water Balance Dashboard.

This module loads the compiled dashboard UI and provides methods to update
KPI values with live data from the database.

Data Sources:
- StorageFacilityService: water sources, storage facilities, capacity, volume, utilization
- EnvironmentalDataService: rainfall, evaporation
- FlowDiagramPage: balance data (inflows, outflows, recirculation, error)
"""

import logging
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QGuiApplication, QFont, QColor
from ui.dashboards.generated_ui_dashboard import Ui_Form
from ui.theme import PALETTE
from services.dashboard_service import get_dashboard_service

logger = logging.getLogger(__name__)


class DashboardPage(QWidget):
    """Water Balance Dashboard page (MAIN KPI OVERVIEW).
    
    Displays 3 sections:
    1. Top KPIs: Water Sources, Storage Facilities, Capacity, Volume, Utilization
    2. Environmental KPIs: Rainfall, Evaporation
    3. Balance Status: Inflows, Outflows, Recirculation, Error, Status
    
    Data Flow:
    - On startup: Loads storage KPIs from database automatically
    - On Refresh: Re-queries database and updates all KPI values
    - On balance update: Receives data from FlowDiagramPage via signal
    
    All values are updated from database via update_data() method.
    """
    
    # Signal emitted when refresh is requested (allows parent to coordinate)
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the Dashboard page (LOAD UI).
        
        Args:
            parent: Parent widget (typically MainWindow's stacked widget)
        """
        super().__init__(parent)
        
        # Load compiled UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # Track current month/year for dynamic date label
        from datetime import datetime
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        # Improve layout spacing and styling (VISUAL ENHANCEMENT)
        self._apply_layout_improvements()
        self._apply_card_shadows()
        
        # Relabel first card: "Water Sources" → "Storage Facilities" (USER REQUEST)
        # This consolidates the two redundant cards into one.
        self.ui.title_water_sources.setText("Storage Facilities")
        
        # Hide the original "Storage Facilities" card (now redundant)
        if hasattr(self.ui, 'card_storage_facilities'):
            self.ui.card_storage_facilities.hide()
        
        # Apply dynamic font scaling based on screen size
        self._apply_dynamic_font_scaling()

        # Clear balance status display so cached UI values do not show on startup
        self._reset_balance_status_display()
        
        # Re-apply fonts when window is resized (connect to parent if available)
        if parent:
            parent.resized.connect(self._apply_dynamic_font_scaling)
        
        # Load initial data from database (replaces placeholder values)
        self._load_initial_data()

    def _reset_balance_status_display(self) -> None:
        self.ui.value_total_inflows.setText("--")
        self.ui.value_total_outflows.setText("--")
        self.ui.value_recirculation.setText("--")
        self.ui.value_balance_error.setText("--")
        self.ui.value_status.setText("--")
        self.ui.value_status.setStyleSheet("")
        if hasattr(self.ui, "label_balance_status"):
            self.ui.label_balance_status.setText("Balance Status | --")
    
    def _load_initial_data(self):
        """Load initial KPI data from database (STARTUP DATA LOAD).
        
        Called during __init__ to populate dashboard with real values.
        Uses DashboardService to aggregate data from multiple sources.
        
        Data loaded:
        - Storage facilities count, capacity, volume from StorageFacilityService
        - Environmental data (rainfall, evaporation) from EnvironmentalDataService
        
        Balance data (inflows, outflows, error) is loaded separately when
        FlowDiagramPage emits balance_data_updated signal.
        """
        try:
            service = get_dashboard_service()
            data = service.get_dashboard_kpis(month=self.current_month, year=self.current_year)
            self.update_data(data)
            logger.info(f"Dashboard loaded initial KPIs: {len(data)} fields")
        except Exception as e:
            logger.warning(f"Could not load initial dashboard data: {e}")
            # Keep placeholder values from Designer if load fails


    def _apply_layout_improvements(self):
        """Improve layout spacing and card margins (VISUAL POLISH).
        
        Adds proper spacing between cards and sections for cleaner, more professional look.
        Fixes centering issues caused by absolute positioning in generated UI.
        Uses CSS margins and padding adjustments.
        """
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
        from PySide6.QtCore import Qt
        
        # Increase spacing in main horizontal layouts (between cards)
        if hasattr(self.ui, 'horizontalLayout'):
            self.ui.horizontalLayout.setSpacing(12)  # Gap between top KPI cards
        
        if hasattr(self.ui, 'layout_environmental_row'):
            self.ui.layout_environmental_row.setSpacing(16)  # Gap between rainfall/evaporation
        
        if hasattr(self.ui, 'layout_balance_row'):
            self.ui.layout_balance_row.setSpacing(12)  # Gap between balance status cards
        
        # Add vertical spacing between sections
        if hasattr(self.ui, 'verticalLayout'):
            self.ui.verticalLayout.setSpacing(16)  # Space between sections
        
        # FIX CENTERING: The generated UI uses absolute positioning for inner widgets.
        # We need to add proper layouts to each card frame so content centers when card expands.
        # Card name -> inner widget name mapping (from generated_ui_dashboard.py)
        card_inner_widgets = {
            'card_water_sources': 'widget',           # Line 71
            'card_storage_facilities': 'widget1',     # Line 144
            'card_total_capacity': 'widget2',         # Line 217
            'card_current_volume': 'widget3',         # Line 291
            'card_utilization': 'widget4',            # Line 365
            'card_evapouration': 'widget5',           # Line 454 (note: inside card_evapouration but has rainfall content)
            'card_rainfall': 'widget6',               # Line 527 (note: inside card_rainfall but has evaporation content)
            'card_total_inflows': 'widget7',          # Line 616
            'card_total_outflows': 'widget8',         # Line 688
            'card_recirculation': 'widget9',          # Line 760
            'card_balance_error': 'widget10',         # Line 832
            'card_status': 'widget11',                # Line 904
        }
        
        for card_name, inner_widget_name in card_inner_widgets.items():
            if hasattr(self.ui, card_name) and hasattr(self.ui, inner_widget_name):
                card = getattr(self.ui, card_name)
                inner_widget = getattr(self.ui, inner_widget_name)
                
                # Check if card already has a layout
                if card.layout() is None:
                    # Add a centering layout to the card frame
                    card_layout = QHBoxLayout(card)
                    card_layout.setContentsMargins(0, 0, 0, 0)
                    card_layout.addWidget(inner_widget, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Improve card appearance with subtle padding
        card_css = f"""
        QFrame {{
            border: 1px solid {PALETTE['border']};
            border-radius: 6px;
            background-color: {PALETTE['surface_alt']};
            margin: 4px;
        }}
        """
        
        # Apply improved styling to all cards
        for card in [
            'card_water_sources', 'card_storage_facilities', 'card_total_capacity',
            'card_current_volume', 'card_utilization', 'card_rainfall',
            'card_evapouration', 'card_total_inflows', 'card_total_outflows',
            'card_recirculation', 'card_balance_error', 'card_status'
        ]:
            if hasattr(self.ui, card):
                card_widget = getattr(self.ui, card)
                # Preserve existing stylesheet and add margin
                current_style = card_widget.styleSheet()
                if 'margin:' not in current_style:
                    # Add margin if not already present
                    if current_style.endswith('}'):
                        new_style = current_style[:-1] + '\nmargin: 4px;\n}'
                        card_widget.setStyleSheet("")

    def _apply_card_shadows(self) -> None:
        """Add subtle elevation to dashboard KPI cards."""
        card_names = [
            'card_water_sources',
            'card_storage_facilities',
            'card_total_capacity',
            'card_current_volume',
            'card_utilization',
            'card_rainfall',
            'card_evapouration',
            'card_total_inflows',
            'card_total_outflows',
            'card_recirculation',
            'card_balance_error',
            'card_status',
        ]
        for card_name in card_names:
            if hasattr(self.ui, card_name):
                card = getattr(self.ui, card_name)
                shadow = QGraphicsDropShadowEffect(card)
                shadow.setBlurRadius(18)
                shadow.setOffset(0, 4)
                shadow.setColor(QColor(16, 32, 64, 45))
                card.setGraphicsEffect(shadow)

    def _apply_dynamic_font_scaling(self) -> None:
        """Scale all dashboard fonts based on current window size (RESPONSIVE FONTS).
        
        Calculates scale factor from screen width and applies proportional
        font sizes to ensure labels and values fit perfectly at any resolution.
        
        Scaling Strategy:
        - Reference: 1920x1080 screen (full HD) = 100% baseline
        - Small screens (1280px): 80% font size
        - Large screens (2560px+): 120% font size
        - Title fonts: 120% of calculated size (emphasis)
        - Value fonts: 100% of calculated size (main data)
        - Label fonts: 90% of calculated size (secondary text)
        
        This ensures all text remains readable and properly proportioned
        regardless of window size or monitor DPI.
        """
        try:
            # Get the primary screen dimensions
            screen = QGuiApplication.primaryScreen()
            if not screen:
                return
            
            # Calculate scale factor based on available screen width
            # Reference: 1920px = 100% (baseline for full HD)
            screen_width = screen.availableGeometry().width()
            base_scale = screen_width / 1920.0
            
            # Clamp scale between 0.75 (min 1280px) and 1.3 (max 2560px)
            scale = max(0.75, min(1.3, base_scale))
            
            # Define base font sizes (optimized for 1920px reference)
            base_title_size = 14       # Section titles
            base_label_size = 11       # Card titles, small labels
            base_value_size = 24       # Main KPI values
            base_unit_size = 10        # Unit labels (m³, %, mm)
            base_date_size = 10        # Date labels
            
            # Calculate actual font sizes with scale factor
            title_size = int(base_title_size * scale * 1.2)      # 20-22px at 1920px
            label_size = int(base_label_size * scale * 0.95)     # 10-11px at 1920px
            value_size = int(base_value_size * scale)            # 24-31px at 1920px
            unit_size = int(base_unit_size * scale)              # 10-13px at 1920px
            date_size = int(base_date_size * scale * 0.95)       # 9-10px at 1920px
            
            # Apply to section/page titles
            for title_widget in ['title_water_sources', 'title_storage_facilities', 
                                'title_total_capacity', 'title_current_volume',
                                'title_utilization', 'title_rainfall', 'title_evaporation',
                                'title_total_inflows', 'title_total_outflows',
                                'title_recirculation', 'title_balance_error', 'title_status']:
                if hasattr(self.ui, title_widget):
                    widget = getattr(self.ui, title_widget)
                    font = widget.font()
                    font.setPointSize(label_size)
                    font.setWeight(QFont.Weight.Medium)
                    widget.setFont(font)
            
            # Apply to KPI value labels (largest font)
            for value_widget in ['value_water_sources', 'value_storage_facilities',
                                'value_total_capacity', 'value_current_volume',
                                'value_utilization', 'value_rainfall', 'value_evaporation',
                                'value_total_inflows', 'value_total_outflows',
                                'value_recirculation', 'value_balance_error', 'value_status']:
                if hasattr(self.ui, value_widget):
                    widget = getattr(self.ui, value_widget)
                    font = widget.font()
                    font.setPointSize(value_size)
                    font.setWeight(QFont.Weight.Bold)
                    widget.setFont(font)
            
            # Apply to unit labels (e.g., "m³", "%", "mm")
            for unit_widget in ['unit_water_sources', 'unit_storage_facilities',
                               'unit_total_capacity', 'unit_current_volume',
                               'unit_utilization', 'unit_rainfall', 'unit_evaporation',
                               'unit_total_inflows', 'unit_total_outflows',
                               'unit_recirculation', 'unit_balance_error', 'unit_status']:
                if hasattr(self.ui, unit_widget):
                    widget = getattr(self.ui, unit_widget)
                    font = widget.font()
                    font.setPointSize(unit_size)
                    widget.setFont(font)
            
            # Apply to date label
            if hasattr(self.ui, 'label_balance_status'):
                widget = self.ui.label_balance_status
                font = widget.font()
                font.setPointSize(date_size)
                widget.setFont(font)
            
            # Apply to section header labels if they exist
            for header_widget in ['label_water_sources', 'label_storage_facilities',
                                 'label_total_capacity', 'label_current_volume',
                                 'label_utilization', 'label_rainfall', 'label_evaporation',
                                 'label_total_inflows', 'label_total_outflows',
                                 'label_recirculation', 'label_balance_error', 'label_status']:
                if hasattr(self.ui, header_widget):
                    widget = getattr(self.ui, header_widget)
                    font = widget.font()
                    font.setPointSize(label_size)
                    widget.setFont(font)
            
            logger.debug(f"Dashboard fonts scaled (scale={scale:.2f}, value_size={value_size}px)")
            
        except Exception as e:
            logger.warning(f"Failed to apply dynamic font scaling: {e}")
    
    def update_data(self, data: dict):
        """Update all dashboard values with live data (PRIMARY UPDATE METHOD).
        
        Args:
            data: Dict containing all KPI values with keys:
                - storage_facilities: int (count of active storage facilities)
                - total_capacity: float (Mm^3)
                - current_volume: float (Mm^3)
                - utilization: float (percentage)
                - rainfall: float (mm)
                - evaporation: float (mm)
                - total_inflows: float (m^3)
                - total_outflows: float (m^3)
                - recirculation: float (m^3)
                - balance_error: float (percentage)
                - status: str (e.g., "Excellent", "Good", "Warning")
                - month: int (1-12, optional - for date label)
                - year: int (optional - for date label)
        
        Example:
            dashboard.update_data({
                'storage_facilities': 10,
                'total_capacity': 15.21,
                'current_volume': 0.83,
                'utilization': 5.5,
                'rainfall': 75,
                'evaporation': 150,
                'total_inflows': 0,
                'total_outflows': 0,
                'recirculation': 0,
                'balance_error': 0.0,
                'status': 'Excellent',
                'month': 12,
                'year': 2025
            })
        """
        # Update date label if month/year provided
        if 'month' in data or 'year' in data:
            month = data.get('month', self.current_month)
            year = data.get('year', self.current_year)
            self.current_month = month
            self.current_year = year
            self._update_date_label(month, year)
        
        # Top KPIs - First card now shows "Storage Facilities" (relabeled from Water Sources)
        # The value_water_sources widget displays storage_facilities count after relabeling
        if 'storage_facilities' in data:
            self.ui.value_water_sources.setText(f"{data['storage_facilities']:,}")
        
        if 'total_capacity' in data:
            self.ui.value_total_capacity.setText(f"{data['total_capacity']:.2f}")
        
        if 'current_volume' in data:
            self.ui.value_current_volume.setText(f"{data['current_volume']:.2f}")
        
        if 'utilization' in data:
            self.ui.value_utilization.setText(f"{data['utilization']:.1f} %")
        
        # Environmental KPIs
        if 'rainfall' in data:
            self.ui.value_rainfall.setText(f"{int(data['rainfall']):,}")
            self.ui.title_rainfall.setText("RainFall")
        else:
            # No data available
            self.ui.value_rainfall.setText("--")
            self.ui.title_rainfall.setText("RainFall (N/A)")
        
        if 'evaporation' in data:
            self.ui.value_evaporation.setText(f"{int(data['evaporation']):,}")
            self.ui.title_evaporation.setText("Evapouration")
        else:
            # No data available
            self.ui.value_evaporation.setText("--")
            self.ui.title_evaporation.setText("Evapouration (N/A)")
        
        # Balance Status
        if 'total_inflows' in data:
            self.ui.value_total_inflows.setText(f"{int(data['total_inflows']):,}")
        
        if 'total_outflows' in data:
            self.ui.value_total_outflows.setText(f"{int(data['total_outflows']):,}")
        
        if 'recirculation' in data:
            self.ui.value_recirculation.setText(f"{int(data['recirculation']):,}")
        
        if 'balance_error' in data:
            error_val = data['balance_error']
            self.ui.value_balance_error.setText(f"{error_val:.2f}")
            
            # Auto-determine status based on error (business rule: <5% excellent, <10% good, >=10% warning)
            if 'status' not in data:
                if error_val < 5.0:
                    status_text = "Excellent"
                    status_color = PALETTE["success"]
                elif error_val < 10.0:
                    status_text = "Good"
                    status_color = PALETTE["warning"]
                else:
                    status_text = "Warning"
                    status_color = PALETTE["danger"]
                
                self.ui.value_status.setText(status_text)
                # Color the status value with matching color
                self.ui.value_status.setStyleSheet("")
            else:
                # Manual status override provided
                self.ui.value_status.setText(data['status'])
                # Determine color from status text
                status_lower = data['status'].lower()
                if 'excellent' in status_lower:
                    status_color = PALETTE["success"]
                elif 'good' in status_lower:
                    status_color = PALETTE["warning"]
                else:
                    status_color = PALETTE["danger"]
                self.ui.value_status.setStyleSheet("")
    
    def _update_date_label(self, month: int, year: int):
        """Update the Balance Status date label (DYNAMIC DATE DISPLAY).
        
        Args:
            month: Month number (1-12)
            year: Year (e.g., 2025)
        """
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_name = month_names[month - 1] if 1 <= month <= 12 else "Unknown"
        date_text = f"Balance Status | {month_name} {year} | "
        self.ui.label_balance_status.setText(date_text)
    
    def refresh(self):
        """Refresh dashboard data from database (CALLED BY REFRESH BUTTON).
        
        Re-queries all data sources and updates the dashboard:
        1. Storage facilities: count, capacity, volume, utilization
        2. Environmental: rainfall, evaporation
        3. Emits refresh_requested signal for parent to coordinate balance data
        
        This is wired to the Refresh button in the main window header.
        """
        logger.info("Dashboard refresh requested")
        
        try:
            # Reload storage and environmental KPIs
            service = get_dashboard_service()
            data = service.get_dashboard_kpis(month=self.current_month, year=self.current_year)
            self.update_data(data)
            logger.info(f"Dashboard refreshed with {len(data)} KPIs")
        except Exception as e:
            logger.error(f"Error refreshing dashboard: {e}", exc_info=True)
        
        # Signal parent to also refresh balance data from flow diagram
        self.refresh_requested.emit()

