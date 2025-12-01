"""
Generate sample Excel templates for data import
"""

import pandas as pd
from pathlib import Path


def create_sample_templates():
    """Create sample Excel files for data import"""
    
    # Create templates directory
    templates_dir = Path(__file__).parent.parent.parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # 1. Water Sources Template
    water_sources_data = {
        'source_code': ['KD', 'GD', 'BH001', 'UG001'],
        'source_name': ['Klipspruit Dam', 'Grootdraai Dam', 'Borehole 1', 'Underground Source 1'],
        'source_type': ['Surface Water', 'Surface Water', 'Groundwater - Borehole', 'Underground - Dewatering'],
        'average_flow_rate': [89167, 550000, 5000, 10000],
        'flow_units': ['m³/month', 'm³/month', 'm³/month', 'm³/month'],
        # Reliability factors as fractions (0-1) per test expectations
        'reliability_factor': [0.80, 0.90, 0.85, 0.75],
        'description': [
            'Main water source from Klipspruit River',
            'Primary storage and supply dam',
            'Production borehole',
            'Underground mine dewatering'
        ],
        'active': [1, 1, 1, 1]
    }
    
    df_sources = pd.DataFrame(water_sources_data)
    sources_file = templates_dir / "water_sources_template.xlsx"
    df_sources.to_excel(sources_file, index=False, sheet_name='Water Sources')
    print(f"✓ Created: {sources_file}")
    
    # 2. Storage Facilities Template
    storage_data = {
        'facility_code': ['TSF', 'RWD', 'PWD', 'FWD'],
        'facility_name': ['Tailings Storage Facility', 'Raw Water Dam', 'Process Water Dam', 'Freshwater Dam'],
        'facility_type': ['Dam', 'Dam', 'Dam', 'Dam'],
        'total_capacity': [8000000, 2000000, 1500000, 960000],
        'surface_area': [800000, 150000, 120000, 80000],
        'minimum_operating_level': [15.0, 20.0, 15.0, 10.0],
        'maximum_operating_level': [90.0, 95.0, 95.0, 95.0],
        'description': [
            'Main tailings storage facility',
            'Raw water storage from external sources',
            'Process water for plant operations',
            'Potable and freshwater storage'
        ],
        'active': [1, 1, 1, 1]
    }
    
    df_storage = pd.DataFrame(storage_data)
    storage_file = templates_dir / "storage_facilities_template.xlsx"
    df_storage.to_excel(storage_file, index=False, sheet_name='Storage Facilities')
    print(f"✓ Created: {storage_file}")
    
    # 3. Measurements Template
    measurements_data = {
        'measurement_date': [
            '2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01',
            '2025-01-02', '2025-01-02', '2025-01-02', '2025-01-02'
        ],
        'measurement_type': [
            'source_flow', 'facility_level', 'source_flow', 'facility_level',
            'source_flow', 'facility_level', 'source_flow', 'facility_level'
        ],
        'source_id': [1, None, 2, None, 1, None, 2, None],
        'facility_id': [None, 1, None, 2, None, 1, None, 2],
        'volume': [89167, 7200000, 550000, 1800000, 89167, 7250000, 550000, 1820000],
        'flow_rate': [89167, None, 550000, None, 89167, None, 550000, None],
        'measured': [1, 1, 1, 1, 1, 1, 1, 1],
        'data_source': ['manual', 'manual', 'manual', 'manual', 'manual', 'manual', 'manual', 'manual']
    }
    
    df_measurements = pd.DataFrame(measurements_data)
    measurements_file = templates_dir / "measurements_template.xlsx"
    df_measurements.to_excel(measurements_file, index=False, sheet_name='Measurements')
    print(f"✓ Created: {measurements_file}")
    
    # 4. Create comprehensive import guide
    guide_text = """
DATA IMPORT TEMPLATES - USER GUIDE
==================================

This directory contains Excel templates for importing data into the Water Balance Application.

AVAILABLE TEMPLATES:
-------------------

1. water_sources_template.xlsx
   - Import water sources (rivers, boreholes, underground sources)
   - Required columns: source_code, source_name, source_type
   - Optional columns: average_flow_rate, flow_units, reliability_factor, description, active

2. storage_facilities_template.xlsx
   - Import storage facilities (dams, tanks, ponds)
   - Required columns: facility_code, facility_name, total_capacity
   - Optional columns: facility_type, surface_area, minimum_operating_level, maximum_operating_level, description, active

3. measurements_template.xlsx
   - Import measurement data (flows, levels, volumes)
   - Required columns: measurement_date, measurement_type
   - Optional columns: source_id, facility_id, volume, flow_rate, measured, data_source

USAGE INSTRUCTIONS:
------------------

1. Open the appropriate template file
2. Fill in your data following the sample format
3. Save the file with a descriptive name
4. In the application, navigate to Import/Export
5. Select the import type matching your data
6. Browse and select your Excel file
7. Click "Preview Data" to validate
8. Click "Import Data" to import into database

DATA VALIDATION:
---------------

- Codes (source_code, facility_code) must be unique
- Dates must be in YYYY-MM-DD format
- Numeric fields (volumes, capacities) must be numbers
- Active field: 1 = active, 0 = inactive
- Do not change column names in templates

TIPS:
-----

- Preview your data before importing
- Start with small batches to verify format
- Check for duplicates before importing
- Backup database before large imports
- Review import results and error messages

For support, refer to the application help documentation.
    """
    
    guide_file = templates_dir / "README.txt"
    with open(guide_file, 'w') as f:
        f.write(guide_text.strip())
    print(f"✓ Created: {guide_file}")
    
    print(f"\n✓ All templates created successfully in: {templates_dir}")
    return templates_dir


if __name__ == "__main__":
    create_sample_templates()
