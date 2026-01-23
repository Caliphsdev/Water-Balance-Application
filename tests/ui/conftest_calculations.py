"""
Shared fixtures and configuration for calculations dashboard tests.

Provides common mocks, test data, and utilities to reduce duplication
across test files.
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.balance_engine import BalanceResult, FreshInflows, DirtyInflows, Outflows, StorageSnapshot, DataQualityFlags


@pytest.fixture
def mock_license_manager():
    """Mock LicenseManager to bypass license checks in tests."""
    with patch('ui.calculations.get_license_manager') as mock_get_license:
        mock_license = Mock()
        # Mock check_calculation_quota method
        mock_license.check_calculation_quota.return_value = (True, "Test quota OK")
        mock_get_license.return_value = mock_license
        yield mock_license


@pytest.fixture
def mock_excel_repo():
    """Mock Excel repository for testing."""
    with patch('ui.calculations.get_default_excel_repo') as mock_repo:
        mock_excel = Mock()
        mock_excel.config.file_path.exists.return_value = True
        mock_excel.config.file_path = Path("c:/test/data.xlsx")
        mock_repo.return_value = mock_excel
        yield mock_excel


@pytest.fixture
def mock_balance_engine():
    """Mock BalanceEngine for testing."""
    with patch('ui.calculations.BalanceEngine') as mock_engine_class:
        mock_engine = Mock()
        # Default engine result
        mock_engine.run.return_value = BalanceResult(
            fresh_in=FreshInflows(total=400000, components={
                'surface_water': 100000,
                'groundwater': 150000,
                'underground': 50000,
                'rainfall': 50000,
                'ore_moisture': 50000,
            }),
            recycled=DirtyInflows(total=100000, components={'rwd_inflow': 100000}),
            outflows=Outflows(total=450000, components={
                'plant_consumption': 300000,
                'dust_suppression': 50000,
                'mining': 40000,
                'domestic': 10000,
                'evaporation': 40000,
                'discharge': 10000,
            }),
            storage=StorageSnapshot(opening=1000000, closing=1050000, source='Database'),
            error_m3=0,
            error_pct=0.0,
            flags=DataQualityFlags(),
            mode='REGULATOR',
            kpis=None
        )
        mock_engine_class.return_value = mock_engine
        yield mock_engine


@pytest.fixture
def mock_legacy_services():
    """Mock LegacyBalanceServices for testing."""
    with patch('ui.calculations.LegacyBalanceServices') as mock_services_class:
        mock_services = Mock()
        mock_services_class.return_value = mock_services
        yield mock_services


@pytest.fixture
def sample_balance_result():
    """Sample balance calculation result for testing."""
    return {
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


@pytest.fixture
def sample_engine_result():
    """Sample BalanceResult from engine for testing."""
    return BalanceResult(
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
        storage=StorageSnapshot(opening=1500000, closing=1550000, source='Database'),
        error_m3=0,
        error_pct=0.0,
        flags=DataQualityFlags(),
        mode='REGULATOR',
        kpis=None
    )


@pytest.fixture
def tkinter_root():
    """Tkinter root window for UI tests."""
    root = tk.Tk()
    root.withdraw()  # Hide window during tests
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass  # Already destroyed


@pytest.fixture
def mock_facilities_data():
    """Sample facilities data from database."""
    return [
        {
            'facility_id': 1,
            'facility_code': 'RWD',
            'facility_name': 'Return Water Dam',
            'total_capacity': 1000000,
            'surface_area': 50000,
            'pump_stop_level': 20.0,
            'evap_active': 1,
        },
        {
            'facility_id': 2,
            'facility_code': 'PWD',
            'facility_name': 'Process Water Dam',
            'total_capacity': 800000,
            'surface_area': 40000,
            'pump_stop_level': 20.0,
            'evap_active': 1,
        },
        {
            'facility_id': 3,
            'facility_code': 'OLDTSF',
            'facility_name': 'Old Tailings Storage Facility',
            'total_capacity': 5000000,
            'surface_area': 200000,
            'pump_stop_level': 10.0,
            'evap_active': 1,
        }
    ]


def create_mock_calculator(balance_result=None):
    """Helper to create mock WaterBalanceCalculator with result."""
    mock_calc = Mock()
    
    if balance_result is None:
        balance_result = {
            'calculation_date': date(2025, 1, 31),
            'inflows': {'total': 100000},
            'outflows': {'total': 90000},
            'storage': {'current_volume': 1000000},
            'storage_change': {'net_storage_change': 10000, 'facilities': {}},
            'closure_error_m3': 0,
            'closure_error_percent': 0.0,
            'balance_status': 'CLOSED',
            'ore_processed': 1000000,
            'pump_transfers': {}
        }
    
    mock_calc.calculate_water_balance.return_value = balance_result
    mock_calc._check_duplicate_calculation.return_value = None
    mock_calc.save_calculation.return_value = 123
    mock_calc.clear_cache.return_value = None
    
    return mock_calc
