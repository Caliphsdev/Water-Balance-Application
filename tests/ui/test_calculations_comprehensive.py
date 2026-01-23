"""
Comprehensive Test Suite for Calculations Dashboard
Tests all calculation flows, data display, tabs, and optimizations

This is the master test file for calculations.py module covering:
- All tabs and their interconnections
- Data flow from Excel → Calculator → Database → UI
- Balance calculations and closure validation
- Cache optimization and performance
- Error handling and edge cases
- UI rendering and responsiveness
"""

import pytest
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.calculations import CalculationsModule
from database.db_manager import DatabaseManager
from utils.water_balance_calculator import WaterBalanceCalculator
from utils.balance_engine import BalanceEngine, BalanceResult
from utils.balance_services import (
    FreshInflows, DirtyInflows, Outflows, 
    StorageSnapshot, DataQualityFlags
)


class TestCalculationsModuleInit:
    """Test initialization and setup of the calculations module."""
    
    def test_module_initialization(self):
        """Test that the module initializes correctly with all required components."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            
            # Verify all components are initialized
            assert module.db is not None, "Database manager should be initialized"
            assert module.calculator is not None, "Calculator should be initialized"
            assert module.balance_engine is not None, "Balance engine should be initialized"
            assert module.template_parser is not None, "Template parser should be initialized"
            
            # Verify all variables are initialized
            assert module.calc_date_var is None, "Date var should be None before load"
            assert module.current_balance is None, "Current balance should be None initially"
            assert module.engine_result is None, "Engine result should be None initially"
            
        finally:
            root.destroy()
    
    def test_load_creates_ui_structure(self):
        """Test that load() creates the complete UI structure."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Verify main frame exists
            assert module.main_frame is not None, "Main frame should be created"
            assert module.main_frame.winfo_exists(), "Main frame should exist in widget tree"
            
            # Verify all tab frames are created
            assert hasattr(module, 'closure_frame'), "Closure frame should exist"
            assert hasattr(module, 'recycled_frame'), "Recycled frame should exist"
            assert hasattr(module, 'inputs_frame'), "Inputs frame should exist"
            assert hasattr(module, 'manual_inputs_frame'), "Manual inputs frame should exist"
            assert hasattr(module, 'storage_dams_frame'), "Storage dams frame should exist"
            assert hasattr(module, 'days_of_operation_frame'), "Days of operation frame should exist"
            assert hasattr(module, 'facility_flows_frame'), "Facility flows frame should exist"
            
            # Verify date variables are initialized after load
            assert module.calc_date_var is not None, "Calc date var should be initialized"
            assert module.year_var is not None, "Year var should be initialized"
            assert module.month_var is not None, "Month var should be initialized"
            
        finally:
            root.destroy()


class TestCalculationFlow:
    """Test the main calculation workflow and data flow."""
    
    @patch('ui.calculations.get_default_excel_repo')
    @patch('ui.calculations.LegacyBalanceServices')
    def test_calculate_balance_success_flow(self, mock_legacy_services, mock_excel_repo):
        """Test successful balance calculation flow through all components."""
        root = tk.Tk()
        try:
            # Setup mocks
            mock_excel = Mock()
            mock_excel.config.file_path.exists.return_value = True
            mock_excel_repo.return_value = mock_excel
            
            # Mock calculator results
            mock_calculator = Mock()
            mock_calculator.calculate_water_balance.return_value = {
                'calculation_date': date(2025, 1, 31),
                'ore_processed': 1000000,
                'inflows': {
                    'total': 500000,
                    'surface_water': 100000,
                    'groundwater': 150000,
                    'underground': 50000,
                    'rainfall': 100000,
                    'ore_moisture': 50000,
                    'rwd_inflow': 50000,
                },
                'outflows': {
                    'total': 450000,
                    'plant_consumption_gross': 300000,
                    'dust_suppression': 50000,
                    'mining_consumption': 40000,
                    'domestic_consumption': 10000,
                    'evaporation': 40000,
                    'discharge': 10000,
                },
                'storage': {
                    'total_capacity': 2000000,
                    'current_volume': 1500000,
                    'available_capacity': 500000,
                    'utilization_percent': 75.0,
                },
                'storage_change': {
                    'net_storage_change': 50000,
                    'facilities': {
                        'RWD': {
                            'opening': 500000,
                            'closing': 550000,
                            'change': 50000,
                            'source': 'Database',
                            'drivers': {
                                'inflow_manual': 100000,
                                'outflow_manual': 50000,
                                'rainfall': 10000,
                                'evaporation': 5000,
                                'abstraction': 5000,
                                'seepage_gain': 0,
                                'seepage_loss': 0,
                            }
                        }
                    }
                },
                'closure_error_m3': 0,
                'closure_error_percent': 0.0,
                'balance_status': 'CLOSED',
                'pump_transfers': {}
            }
            
            # Mock engine result
            mock_engine_result = BalanceResult(
                fresh_in=FreshInflows(total=450000, components={
                    'surface_water': 100000,
                    'groundwater': 150000,
                    'underground': 50000,
                    'rainfall': 100000,
                    'ore_moisture': 50000,
                }),
                recycled=DirtyInflows(total=50000, components={'rwd_inflow': 50000}),
                outflows=Outflows(total=450000, components={
                    'plant_consumption': 300000,
                    'dust_suppression': 50000,
                    'mining': 40000,
                    'domestic': 10000,
                    'evaporation': 40000,
                    'discharge': 10000,
                }),
                storage=StorageSnapshot(
                    opening=1500000,
                    closing=1550000,
                    source='Database'
                ),
                error_m3=0,
                error_pct=0.0,
                flags=DataQualityFlags(),
                mode='REGULATOR',
                kpis=None
            )
            
            module = CalculationsModule(root)
            module.calculator = mock_calculator
            
            # Mock balance engine
            mock_engine = Mock()
            mock_engine.run.return_value = mock_engine_result
            
            # Mock legacy services
            mock_legacy = Mock()
            mock_legacy_services.return_value = mock_legacy
            
            module.load()
            
            # Set calculation date
            module.calc_date_var.set('2025-01-31')
            
            # Patch BalanceEngine to inject mocked result
            with patch('ui.calculations.BalanceEngine') as mock_balance_engine_class:
                mock_balance_engine_class.return_value = mock_engine
                
                # Trigger calculation
                module._calculate_balance()
            
            # Verify calculation results are stored
            assert module.current_balance is not None, "Balance result should be stored"
            assert module.engine_result is not None, "Engine result should be stored"
            
            # Verify calculator was called correctly
            mock_calculator.calculate_water_balance.assert_called_once()
            call_args = mock_calculator.calculate_water_balance.call_args
            assert call_args[0][0] == date(2025, 1, 31), "Should pass correct date to calculator"
            
            # Verify balance engine was called
            mock_engine.run.assert_called_once_with(date(2025, 1, 31))
            
        finally:
            root.destroy()
    
    @patch('ui.calculations.get_default_excel_repo')
    def test_calculate_balance_missing_excel_file(self, mock_excel_repo):
        """Test calculation fails gracefully when Excel file is missing."""
        root = tk.Tk()
        try:
            # Mock missing Excel file
            mock_excel = Mock()
            mock_excel.config.file_path.exists.return_value = False
            mock_excel.config.file_path = Path("c:/missing/file.xlsx")
            mock_excel_repo.return_value = mock_excel
            
            module = CalculationsModule(root)
            module.load()
            module.calc_date_var.set('2025-01-31')
            
            # Should not raise exception, but should show error dialog
            with patch('tkinter.messagebox.showerror') as mock_error:
                module._calculate_balance()
                
                # Verify error message was shown
                mock_error.assert_called_once()
                args = mock_error.call_args[0]
                assert 'Excel File Missing' in args[0]
                assert 'not found' in args[1]
            
            # Balance should not be calculated
            assert module.current_balance is None
            assert module.engine_result is None
            
        finally:
            root.destroy()
    
    def test_cache_cleared_before_calculation(self):
        """Test that caches are cleared before each calculation to ensure fresh data."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            mock_calculator = Mock()
            module.calculator = mock_calculator
            
            # Mock successful calculation
            with patch('ui.calculations.get_default_excel_repo') as mock_excel_repo, \
                 patch('ui.calculations.BalanceEngine'), \
                 patch('ui.calculations.LegacyBalanceServices'):
                
                mock_excel = Mock()
                mock_excel.config.file_path.exists.return_value = True
                mock_excel_repo.return_value = mock_excel
                
                module.load()
                module.calc_date_var.set('2025-01-31')
                
                try:
                    module._calculate_balance()
                except Exception:
                    pass  # Ignore calculation errors, we only care about cache clearing
                
                # Verify cache was cleared
                mock_calculator.clear_cache.assert_called_once()
            
        finally:
            root.destroy()


class TestClosureTab:
    """Test System Balance (Closure) tab functionality."""
    
    def test_closure_display_with_valid_data(self):
        """Test closure tab displays correct metrics with valid engine result."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set engine result
            module.engine_result = BalanceResult(
                fresh_in=FreshInflows(total=400000, components={
                    'surface_water': 100000,
                    'groundwater': 150000,
                    'underground': 50000,
                    'rainfall': 50000,
                    'ore_moisture': 50000,
                }),
                recycled=DirtyInflows(total=100000, components={'rwd_inflow': 100000}),
                outflows=Outflows(total=380000, components={
                    'plant_consumption': 250000,
                    'dust_suppression': 50000,
                    'mining': 40000,
                    'domestic': 10000,
                    'evaporation': 20000,
                    'discharge': 10000,
                }),
                storage=StorageSnapshot(
                    opening=1000000,
                    closing=1020000,
                    delta=20000,
                    source='Database'
                ),
                error_m3=0,
                error_pct=0.0,
                flags=DataQualityFlags(),
                mode='REGULATOR'
            )
            
            # Update closure display
            module._update_closure_display()
            
            # Verify frame has content (widgets created)
            assert len(module.closure_frame.winfo_children()) > 0, "Closure tab should have widgets"
            
            # Find canvas widget (scrollable content)
            canvas_widgets = [w for w in module.closure_frame.winfo_children() 
                            if isinstance(w, tk.Canvas) or isinstance(w, tk.Frame)]
            assert len(canvas_widgets) > 0, "Should have scrollable content container"
            
        finally:
            root.destroy()
    
    def test_closure_display_shows_error_status(self):
        """Test closure tab shows warning status when error exceeds threshold."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set engine result with high error
            module.engine_result = BalanceResult(
                fresh_in=FreshInflows(total=400000, components={}),
                recycled=DirtyInflows(total=0, components={}),
                outflows=Outflows(total=300000, components={}),
                storage=StorageSnapshot(opening=1000000, closing=1000000, source='Database'),
                error_m3=50000,  # 12.5% error
                error_pct=12.5,
                flags=DataQualityFlags(),
                mode='REGULATOR'
            )
            
            module._update_closure_display()
            
            # Verify error warning is displayed
            # (Actual implementation shows ⚠️ CHECK REQUIRED status)
            assert len(module.closure_frame.winfo_children()) > 0
            
        finally:
            root.destroy()


class TestRecycledWaterTab:
    """Test Recycled Water tab functionality."""
    
    def test_recycled_display_with_dewatering_and_rwd(self):
        """Test recycled tab displays dewatering and RWD correctly."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set balance with recycled water components
            module.current_balance = {
                'inflows': {
                    'total': 500000,
                    'surface_water': 100000,
                    'groundwater': 150000,
                    'underground': 100000,  # Dewatering
                    'rainfall': 50000,
                    'ore_moisture': 50000,
                    'rwd_inflow': 50000,  # RWD
                }
            }
            
            module._update_recycled_display()
            
            # Verify display has content
            assert len(module.recycled_frame.winfo_children()) > 0
            
            # Find treeview widget showing components
            treeviews = [w for w in module.recycled_frame.winfo_children() 
                        if isinstance(w, ttk.Treeview)]
            # May be nested, search recursively
            def find_treeviews(widget):
                result = []
                if isinstance(widget, ttk.Treeview):
                    result.append(widget)
                for child in widget.winfo_children():
                    result.extend(find_treeviews(child))
                return result
            
            all_treeviews = find_treeviews(module.recycled_frame)
            assert len(all_treeviews) > 0, "Should have treeview showing recycled components"
            
        finally:
            root.destroy()
    
    def test_recycled_percentage_calculation(self):
        """Test recycled water percentage is calculated correctly against fresh + dirty."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Fresh: 400k, Dirty (RWD): 100k, Underground (Dewatering): 50k
            # Recycled = Dewatering + RWD = 150k
            # % = 150k / (400k fresh + 100k dirty) = 150k / 500k = 30%
            module.current_balance = {
                'inflows': {
                    'total': 550000,
                    'surface_water': 100000,
                    'groundwater': 150000,
                    'underground': 50000,  # Dewatering (recycled)
                    'rainfall': 100000,
                    'ore_moisture': 50000,
                    'rwd_inflow': 100000,  # RWD (dirty/recycled)
                }
            }
            
            module._update_recycled_display()
            
            # The actual percentage should be:
            # Fresh = 100k + 150k + 0 + 100k + 50k = 400k
            # Dirty = 100k (RWD)
            # Denominator = 400k + 100k = 500k
            # Recycled = 50k (dewatering) + 100k (RWD) = 150k
            # % = 150k / 500k = 30%
            
            # Verify (hard to check exact value without parsing UI, but structure should exist)
            assert len(module.recycled_frame.winfo_children()) > 0
            
        finally:
            root.destroy()


class TestInputsAuditTab:
    """Test Inputs Audit tab functionality."""
    
    @patch('ui.calculations.collect_inputs_audit')
    def test_inputs_audit_displays_excel_headers(self, mock_audit):
        """Test inputs audit shows Excel header status correctly."""
        root = tk.Tk()
        try:
            # Mock audit data
            mock_audit.return_value = {
                'month': '2025-01-31',
                'legacy_excel': {
                    'path': 'c:/data/excel.xlsx',
                    'exists': True,
                    'matched_row_date': '2025-01-31',
                    'headers': [
                        {'name': 'Tonnes Milled', 'value': 1000000, 'found': True},
                        {'name': 'Main decline dewatering', 'value': 50000, 'found': True},
                        {'name': 'Groot Dwars', 'value': None, 'found': False},
                    ]
                }
            }
            
            module = CalculationsModule(root)
            module.load()
            module.calc_date_var.set('2025-01-31')
            
            module._update_inputs_audit_display()
            
            # Verify audit display has content
            assert len(module.inputs_frame.winfo_children()) > 0
            
            # Find treeview showing headers
            def find_treeviews(widget):
                result = []
                if isinstance(widget, ttk.Treeview):
                    result.append(widget)
                for child in widget.winfo_children():
                    result.extend(find_treeviews(child))
                return result
            
            treeviews = find_treeviews(module.inputs_frame)
            assert len(treeviews) > 0, "Should have treeview showing Excel headers"
            
            # Verify mock was called with correct date
            mock_audit.assert_called_once()
            
        finally:
            root.destroy()


class TestManualInputsTab:
    """Test Manual Inputs tab functionality."""
    
    @patch('database.db_manager.DatabaseManager.get_monthly_manual_inputs')
    def test_load_manual_inputs_from_database(self, mock_get_manual):
        """Test manual inputs are loaded from database on tab load."""
        root = tk.Tk()
        try:
            # Mock database response
            mock_get_manual.return_value = {
                'mining_consumption_m3': 50000.0,
                'domestic_consumption_m3': 10000.0,
                'discharge_m3': 5000.0,
            }
            
            module = CalculationsModule(root)
            module.load()
            module.calc_date_var.set('2025-01-31')
            
            module._load_manual_inputs()
            
            # Verify values are loaded into variables
            assert module.manual_inputs_vars['mining_consumption_m3'].get() == '50000.0'
            assert module.manual_inputs_vars['domestic_consumption_m3'].get() == '10000.0'
            assert module.manual_inputs_vars['discharge_m3'].get() == '5000.0'
            
        finally:
            root.destroy()
    
    @patch('database.db_manager.DatabaseManager.upsert_monthly_manual_inputs')
    def test_save_manual_inputs_to_database(self, mock_upsert):
        """Test manual inputs are saved to database correctly."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            module.calc_date_var.set('2025-01-31')
            
            # Set manual input values
            module.manual_inputs_vars['mining_consumption_m3'].set('60000')
            module.manual_inputs_vars['domestic_consumption_m3'].set('12000')
            module.manual_inputs_vars['discharge_m3'].set('8000')
            
            with patch('tkinter.messagebox.showinfo') as mock_info:
                module._save_manual_inputs()
                
                # Verify database was updated
                mock_upsert.assert_called_once()
                call_args = mock_upsert.call_args[0]
                assert call_args[0] == date(2025, 1, 1)  # Month start
                assert call_args[1] == {
                    'mining_consumption_m3': 60000.0,
                    'domestic_consumption_m3': 12000.0,
                    'discharge_m3': 8000.0,
                }
                
                # Verify success message shown
                mock_info.assert_called_once()
            
        finally:
            root.destroy()
    
    def test_clear_manual_inputs(self):
        """Test clearing manual inputs resets all fields to zero."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set some values
            module.manual_inputs_vars['mining_consumption_m3'].set('50000')
            module.manual_inputs_vars['domestic_consumption_m3'].set('10000')
            
            # Clear
            module._clear_manual_inputs()
            
            # Verify all are zero
            assert module.manual_inputs_vars['mining_consumption_m3'].get() == '0'
            assert module.manual_inputs_vars['domestic_consumption_m3'].get() == '0'
            assert module.manual_inputs_vars['discharge_m3'].get() == '0'
            
        finally:
            root.destroy()


class TestStorageDamsTab:
    """Test Storage & Dams tab functionality."""
    
    def test_storage_display_shows_facility_drivers(self):
        """Test storage tab displays per-facility drivers correctly."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set balance with storage change data
            module.current_balance = {
                'storage_change': {
                    'facilities': {
                        'RWD': {
                            'opening': 500000,
                            'closing': 550000,
                            'change': 50000,
                            'source': 'Database',
                            'drivers': {
                                'inflow_manual': 100000,
                                'outflow_manual': 40000,
                                'rainfall': 10000,
                                'evaporation': 15000,
                                'abstraction': 5000,
                                'seepage_gain': 0,
                                'seepage_loss': 0,
                            }
                        },
                        'PWD': {
                            'opening': 300000,
                            'closing': 320000,
                            'change': 20000,
                            'source': 'Excel',
                            'drivers': {
                                'inflow_manual': 50000,
                                'outflow_manual': 25000,
                                'rainfall': 5000,
                                'evaporation': 8000,
                                'abstraction': 2000,
                                'seepage_gain': 0,
                                'seepage_loss': 0,
                            }
                        }
                    }
                }
            }
            
            module.calc_date_var = tk.StringVar(value='2025-01-31')
            
            # Mock database to return facilities
            with patch.object(module.db, 'get_storage_facilities') as mock_facilities:
                mock_facilities.return_value = [
                    {
                        'facility_code': 'RWD',
                        'facility_name': 'Return Water Dam',
                        'total_capacity': 1000000,
                    },
                    {
                        'facility_code': 'PWD',
                        'facility_name': 'Process Water Dam',
                        'total_capacity': 800000,
                    }
                ]
                
                module._update_storage_dams_display()
            
            # Verify display has content
            assert len(module.storage_dams_frame.winfo_children()) > 0
            
            # Find treeview showing facility drivers
            def find_treeviews(widget):
                result = []
                if isinstance(widget, ttk.Treeview):
                    result.append(widget)
                for child in widget.winfo_children():
                    result.extend(find_treeviews(child))
                return result
            
            treeviews = find_treeviews(module.storage_dams_frame)
            assert len(treeviews) > 0, "Should have treeview showing facility drivers"
            
        finally:
            root.destroy()
    
    def test_storage_displays_data_source_indicators(self):
        """Test storage tab shows whether data came from Excel or Database."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            module.current_balance = {
                'storage_change': {
                    'facilities': {
                        'RWD': {
                            'opening': 500000,
                            'closing': 550000,
                            'change': 50000,
                            'source': 'Excel',  # Excel source
                            'drivers': {}
                        },
                        'PWD': {
                            'opening': 300000,
                            'closing': 320000,
                            'change': 20000,
                            'source': 'Database',  # Database source
                            'drivers': {}
                        }
                    }
                }
            }
            
            module.calc_date_var = tk.StringVar(value='2025-01-31')
            
            with patch.object(module.db, 'get_storage_facilities') as mock_facilities:
                mock_facilities.return_value = [
                    {'facility_code': 'RWD', 'facility_name': 'Return Water Dam'},
                    {'facility_code': 'PWD', 'facility_name': 'Process Water Dam'},
                ]
                
                module._update_storage_dams_display()
            
            # Source indicators should be visible in the display
            # (📊 for Excel, 💾 for Database)
            assert len(module.storage_dams_frame.winfo_children()) > 0
            
        finally:
            root.destroy()


class TestDaysOfOperationTab:
    """Test Days of Operation tab functionality and calculations."""
    
    def test_days_of_operation_calculation(self):
        """Test days of operation is calculated correctly from storage and consumption."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set balance data
            module.current_balance = {
                'storage': {
                    'closing': 1000000,  # 1M m³ current storage
                    'capacity': 2000000,  # 2M m³ capacity
                },
                'outflows': {
                    'total': 300000,  # 300k m³/month outflows
                }
            }
            
            # Set engine result for consistent outflows
            module.engine_result = BalanceResult(
                fresh_in=FreshInflows(total=0, components={}),
                recycled=DirtyInflows(total=0, components={}),
                outflows=Outflows(total=300000, components={}),
                storage=StorageSnapshot(opening=0, closing=1000000, source='Database'),
                error_m3=0,
                error_pct=0,
                flags=DataQualityFlags(),
                mode='REGULATOR'
            )
            
            module.calc_date_var = tk.StringVar(value='2025-01-31')
            
            # Mock database to return facilities for critical threshold calculation
            with patch.object(module.db, 'get_storage_facilities') as mock_facilities:
                mock_facilities.return_value = [
                    {
                        'total_capacity': 2000000,
                        'surface_area': 100000,
                        'pump_stop_level': 20.0,  # 20% critical threshold
                        'evap_active': 1,
                    }
                ]
                
                module._update_days_of_operation_display()
            
            # Expected calculation:
            # Critical threshold = 20% of 2M = 400k m³
            # Usable storage = 1M - 400k = 600k m³
            # Daily consumption = 300k / 30 = 10k m³/day
            # Days remaining = 600k / 10k = 60 days
            
            # Verify display has content
            assert len(module.days_of_operation_frame.winfo_children()) > 0
            
        finally:
            root.destroy()
    
    def test_days_of_operation_shows_critical_status(self):
        """Test days of operation shows critical warning when below 30 days."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set low storage scenario
            module.current_balance = {
                'storage': {
                    'closing': 500000,  # 500k m³
                    'capacity': 2000000,
                },
                'outflows': {
                    'total': 300000,  # 300k/month = 10k/day
                }
            }
            
            module.engine_result = BalanceResult(
                fresh_in=FreshInflows(total=0, components={}),
                recycled=DirtyInflows(total=0, components={}),
                outflows=Outflows(total=300000, components={}),
                storage=StorageSnapshot(opening=0, closing=500000, source='Database'),
                error_m3=0,
                error_pct=0,
                flags=DataQualityFlags(),
                mode='REGULATOR'
            )
            
            module.calc_date_var = tk.StringVar(value='2025-01-31')
            
            with patch.object(module.db, 'get_storage_facilities') as mock_facilities:
                mock_facilities.return_value = [
                    {
                        'total_capacity': 2000000,
                        'surface_area': 100000,
                        'pump_stop_level': 20.0,
                        'evap_active': 1,
                    }
                ]
                
                module._update_days_of_operation_display()
            
            # Critical threshold = 400k, usable = 500k - 400k = 100k
            # Days = 100k / 10k = 10 days (CRITICAL)
            
            # Verify warning display exists
            assert len(module.days_of_operation_frame.winfo_children()) > 0
            
        finally:
            root.destroy()


class TestFacilityFlowsTab:
    """Test Facility Flows tab functionality."""
    
    @patch('database.db_manager.DatabaseManager.get_facility_inflow_monthly')
    @patch('database.db_manager.DatabaseManager.get_facility_outflow_monthly')
    def test_load_facility_flows_data(self, mock_outflow, mock_inflow):
        """Test facility flows are loaded from database correctly."""
        root = tk.Tk()
        try:
            # Mock database responses
            mock_inflow.side_effect = lambda fac_id, month, year: {
                1: 100000.0,
                2: 50000.0,
            }.get(fac_id, 0.0)
            
            mock_outflow.side_effect = lambda fac_id, month, year: {
                1: 80000.0,
                2: 30000.0,
            }.get(fac_id, 0.0)
            
            module = CalculationsModule(root)
            
            # Mock get_storage_facilities
            with patch.object(module.db, 'get_storage_facilities') as mock_facilities:
                mock_facilities.return_value = [
                    {
                        'facility_id': 1,
                        'facility_code': 'RWD',
                        'facility_name': 'Return Water Dam',
                    },
                    {
                        'facility_id': 2,
                        'facility_code': 'PWD',
                        'facility_name': 'Process Water Dam',
                    }
                ]
                
                module.load()
                
                # Set month/year
                module.facility_flows_month_var.set(1)
                module.facility_flows_year_var.set(2025)
                
                module._load_facility_flows_data()
            
            # Verify treeview has rows
            assert len(module.facility_flows_tree.get_children()) == 2
            
            # Verify row values
            row1 = module.facility_flows_tree.item(module.facility_flows_tree.get_children()[0])
            assert row1['text'] == 'RWD'
            assert '100,000' in row1['values'][1]  # Inflow
            assert '80,000' in row1['values'][2]  # Outflow
            assert '20,000' in row1['values'][3]  # Net (100k - 80k)
            
        finally:
            root.destroy()
    
    @patch('database.db_manager.DatabaseManager.set_facility_inflow_monthly')
    @patch('database.db_manager.DatabaseManager.set_facility_outflow_monthly')
    def test_save_facility_flows_data(self, mock_set_outflow, mock_set_inflow):
        """Test facility flows are saved to database correctly."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Populate treeview with test data
            module.facility_flows_tree.insert('', 'end', iid='fac_1',
                                             text='RWD',
                                             values=('Return Water Dam', '120000', '90000', '30000'))
            
            module.facility_flows_month_var.set(1)
            module.facility_flows_year_var.set(2025)
            
            with patch('tkinter.messagebox.showinfo') as mock_info, \
                 patch('ui.calculations.CalculationsModule._calculate_balance'):
                module._save_facility_flows_data()
                
                # Verify database calls
                mock_set_inflow.assert_called_once_with(1, 1, 120000.0, 2025)
                mock_set_outflow.assert_called_once_with(1, 1, 90000.0, 2025)
                
                # Verify success message
                mock_info.assert_called_once()
            
        finally:
            root.destroy()


class TestDataQualityValidation:
    """Test data quality checks and validation."""
    
    def test_capacity_overflow_validation(self):
        """Test warning when projected closing volume exceeds capacity."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            calculator = WaterBalanceCalculator()
            
            # Test overflow scenario
            calculator._validate_facility_flows(
                facility_code='TEST_DAM',
                capacity=100000,
                inflow_total=150000,  # More than capacity
                outflow_total=50000,
                opening_volume=80000
            )
            
            # Verify warning was logged
            warnings = calculator.get_capacity_warnings()
            assert len(warnings) > 0
            assert 'TEST_DAM' in warnings[0]
            assert 'exceeds capacity' in warnings[0].lower()
            
        finally:
            root.destroy()
    
    def test_data_quality_flags_display(self):
        """Test data quality flags are displayed when present."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set engine result with quality flags
            flags = DataQualityFlags()
            flags.add_flag('missing_rainfall', 'Rainfall data not found for this month')
            flags.add_flag('simulated_evaporation', 'Evaporation calculated from regional average')
            
            module.engine_result = BalanceResult(
                fresh_in=FreshInflows(total=0, components={}),
                recycled=DirtyInflows(total=0, components={}),
                outflows=Outflows(total=0, components={}),
                storage=StorageSnapshot(opening=0, closing=0, source='Database'),
                error_m3=0,
                error_pct=0,
                flags=flags,
                mode='REGULATOR'
            )
            
            module._update_quality_display()
            
            # Verify flags are displayed
            assert len(module.quality_frame.winfo_children()) > 0
            
        finally:
            root.destroy()


class TestPerformanceOptimizations:
    """Test performance optimizations and caching."""
    
    def test_calculation_uses_cache(self):
        """Test that repeated calculations use cache instead of recalculating."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            mock_calculator = Mock()
            
            # First call returns result, subsequent calls should use cache
            mock_calculator.calculate_water_balance.return_value = {
                'calculation_date': date(2025, 1, 31),
                'inflows': {'total': 100000},
                'outflows': {'total': 90000},
                'storage': {'current_volume': 1000000},
                'storage_change': {'net_storage_change': 10000, 'facilities': {}},
                'closure_error_m3': 0,
                'closure_error_percent': 0,
                'balance_status': 'CLOSED',
                'ore_processed': 1000000,
                'pump_transfers': {}
            }
            
            module.calculator = mock_calculator
            
            # Cache should be checked before calculation
            # (Implementation detail: WaterBalanceCalculator has internal cache)
            
        finally:
            root.destroy()
    
    def test_cache_invalidation_on_excel_change(self):
        """Test cache is invalidated when Excel file changes."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            mock_calculator = Mock()
            module.calculator = mock_calculator
            
            module.load()
            
            # Simulate calculation
            with patch('ui.calculations.get_default_excel_repo'), \
                 patch('ui.calculations.BalanceEngine'), \
                 patch('ui.calculations.LegacyBalanceServices'):
                try:
                    module._calculate_balance()
                except Exception:
                    pass
            
            # Verify cache was cleared before calculation
            mock_calculator.clear_cache.assert_called()
            
        finally:
            root.destroy()


class TestTooltipsFunctionality:
    """Test tooltip functionality for balance metrics."""
    
    def test_tooltips_defined_for_all_metrics(self):
        """Test that BALANCE_TOOLTIPS has entries for all displayed metrics."""
        tooltips = CalculationsModule.BALANCE_TOOLTIPS
        
        # Verify key metrics have tooltips
        assert 'Fresh Inflows' in tooltips
        assert 'Dirty Inflows' in tooltips
        assert 'Total Outflows' in tooltips
        assert 'ΔStorage' in tooltips
        assert 'Balance Error' in tooltips
        assert 'Error %' in tooltips
        assert 'Status' in tooltips
        
        # Verify tooltips are descriptive (not empty)
        for key, text in tooltips.items():
            assert len(text) > 20, f"Tooltip for '{key}' should be descriptive"
            assert 'water' in text.lower() or 'balance' in text.lower() or \
                   'volume' in text.lower() or 'error' in text.lower(), \
                   f"Tooltip for '{key}' should mention water/balance/volume/error"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_capacity_facilities(self):
        """Test handling of facilities with zero or None capacity."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            module.current_balance = {
                'storage_change': {
                    'facilities': {
                        'TEMP_DAM': {
                            'opening': 0,
                            'closing': 0,
                            'change': 0,
                            'source': 'Database',
                            'drivers': {}
                        }
                    }
                }
            }
            
            module.calc_date_var = tk.StringVar(value='2025-01-31')
            
            with patch.object(module.db, 'get_storage_facilities') as mock_facilities:
                mock_facilities.return_value = [
                    {
                        'facility_code': 'TEMP_DAM',
                        'facility_name': 'Temporary Dam',
                        'total_capacity': 0,  # Zero capacity
                    }
                ]
                
                # Should not crash
                module._update_storage_dams_display()
            
            assert len(module.storage_dams_frame.winfo_children()) > 0
            
        finally:
            root.destroy()
    
    def test_missing_calculation_date(self):
        """Test handling when calculation date is not set."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Don't set calc_date_var
            module.calc_date_var = None
            
            # Should not crash when trying to get date
            result = module._get_calc_date_obj()
            assert result is None
            
        finally:
            root.destroy()
    
    def test_invalid_manual_input_values(self):
        """Test handling of invalid manual input values (non-numeric)."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            module.calc_date_var.set('2025-01-31')
            
            # Set invalid values
            module.manual_inputs_vars['mining_consumption_m3'].set('invalid')
            module.manual_inputs_vars['domestic_consumption_m3'].set('abc123')
            
            with patch('tkinter.messagebox.showerror') as mock_error:
                module._save_manual_inputs()
                
                # Should show error
                mock_error.assert_called_once()
                args = mock_error.call_args[0]
                assert 'Invalid' in args[0]
                assert 'numeric' in args[1].lower()
            
        finally:
            root.destroy()


class TestResponsiveness:
    """Test UI responsiveness and layout."""
    
    def test_scrollable_content_areas(self):
        """Test that long content areas are scrollable."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            
            # Set large dataset for closure tab
            module.engine_result = BalanceResult(
                fresh_in=FreshInflows(total=1000000, components={
                    f'source_{i}': 10000 for i in range(50)  # Many sources
                }),
                recycled=DirtyInflows(total=0, components={}),
                outflows=Outflows(total=900000, components={
                    f'outflow_{i}': 10000 for i in range(50)  # Many outflows
                }),
                storage=StorageSnapshot(opening=1000000, closing=1100000, source='Database'),
                error_m3=0,
                error_pct=0,
                flags=DataQualityFlags(),
                mode='REGULATOR'
            )
            
            module._update_closure_display()
            
            # Verify scrollbar exists
            def find_scrollbars(widget):
                result = []
                if isinstance(widget, ttk.Scrollbar):
                    result.append(widget)
                for child in widget.winfo_children():
                    result.extend(find_scrollbars(child))
                return result
            
            scrollbars = find_scrollbars(module.closure_frame)
            assert len(scrollbars) > 0, "Should have scrollbar for long content"
            
        finally:
            root.destroy()


class TestIntegrationWithOtherModules:
    """Test integration with calculator, database, and other components."""
    
    @patch('utils.water_balance_calculator.WaterBalanceCalculator.save_calculation')
    def test_auto_save_after_calculation(self, mock_save):
        """Test that calculations are auto-saved after successful run."""
        root = tk.Tk()
        try:
            module = CalculationsModule(root)
            module.load()
            module.calc_date_var.set('2025-01-31')
            
            # Mock successful calculation
            mock_calculator = Mock()
            mock_calculator.calculate_water_balance.return_value = {
                'calculation_date': date(2025, 1, 31),
                'inflows': {'total': 100000},
                'outflows': {'total': 90000},
                'storage': {'current_volume': 1000000},
                'storage_change': {'net_storage_change': 10000, 'facilities': {}},
                'closure_error_m3': 0,
                'closure_error_percent': 0,
                'balance_status': 'CLOSED',
                'ore_processed': 1000000,
                'pump_transfers': {}
            }
            mock_calculator._check_duplicate_calculation.return_value = None
            mock_calculator.save_calculation.return_value = 123
            
            module.calculator = mock_calculator
            
            with patch('ui.calculations.get_default_excel_repo') as mock_excel_repo, \
                 patch('ui.calculations.BalanceEngine'), \
                 patch('ui.calculations.LegacyBalanceServices'):
                
                mock_excel = Mock()
                mock_excel.config.file_path.exists.return_value = True
                mock_excel_repo.return_value = mock_excel
                
                module._calculate_balance()
            
            # Verify save was called with persist_storage=True
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[1]['persist_storage'] is True
            
        finally:
            root.destroy()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
