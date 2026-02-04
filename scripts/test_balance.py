"""Test script for balance service calculation.

Tests the updated BalanceService with real data from the database and Excel.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import date
from services.calculation.models import CalculationPeriod
from services.calculation.balance_service import BalanceService


def main():
    # Test with September 2025 which has both environmental and Excel data
    period = CalculationPeriod(year=2025, month=9)
    
    print('Creating BalanceService...')
    service = BalanceService()
    
    print('Running calculation...')
    result = service.calculate(period)
    
    print(f'\n=== Balance Result for {period.period_label} ===')
    print(f'Fresh Inflows: {result.inflows.total_m3:,.0f} m3')
    rainfall = result.inflows.components.get('rainfall', 0)
    runoff = result.inflows.components.get('runoff', 0)
    surface_water = result.inflows.components.get('surface_water', 0)
    groundwater = result.inflows.components.get('groundwater', 0)
    dewatering = result.inflows.components.get('dewatering', 0)
    ore_moisture = result.inflows.components.get('ore_moisture', 0)
    print(f'  - Rainfall (direct): {rainfall:,.0f} m3')
    print(f'  - Runoff (catchment): {runoff:,.0f} m3')
    print(f'  - Surface water (rivers): {surface_water:,.0f} m3')
    print(f'  - Groundwater (boreholes): {groundwater:,.0f} m3')
    print(f'  - Underground dewatering: {dewatering:,.0f} m3')
    print(f'  - Ore moisture: {ore_moisture:,.0f} m3')
    
    print(f'\nOutflows: {result.outflows.total_m3:,.0f} m3')
    evap = result.outflows.components.get('evaporation', 0)
    seepage = result.outflows.components.get('seepage', 0)
    dust = result.outflows.components.get('dust_suppression', 0)
    tailings = result.outflows.components.get('tailings_lockup', 0)
    mining = result.outflows.components.get('mining_consumption', 0)
    domestic = result.outflows.components.get('domestic_consumption', 0)
    product = result.outflows.components.get('product_moisture', 0)
    print(f'  - Evaporation: {evap:,.0f} m3')
    print(f'  - Seepage: {seepage:,.0f} m3')
    print(f'  - Dust suppression: {dust:,.0f} m3')
    print(f'  - Tailings lockup: {tailings:,.0f} m3')
    print(f'  - Mining consumption: {mining:,.0f} m3')
    print(f'  - Domestic consumption: {domestic:,.0f} m3')
    print(f'  - Product moisture: {product:,.0f} m3')
    
    print(f'\nStorage Change: {result.storage.delta_m3:,.0f} m3')
    print(f'  - Opening: {result.storage.opening_m3:,.0f} m3')
    print(f'  - Closing: {result.storage.closing_m3:,.0f} m3')
    
    print(f'\nRecycled: {result.recycled.total_m3:,.0f} m3')
    print(f'\nBalance Error: {result.balance_error_m3:,.0f} m3 ({result.error_pct:.2f}%)')
    print(f'Status: {result.status}')
    
    if result.quality_flags.has_issues:
        print('\n=== Data Quality Flags ===')
        print(f'  Issues: {result.quality_flags.issue_count}')


if __name__ == '__main__':
    main()
