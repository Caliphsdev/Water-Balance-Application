"""
Database Population Script
Populates database with actual TRP water balance data from our analysis
"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager


def populate_water_sources(db: DatabaseManager):
    """Add all 18 water sources identified in analysis"""
    
    print("\n📥 Adding Water Sources...")
    
    # Get type IDs
    types = {t['type_code']: t['type_id'] for t in db.get_water_source_types()}
    areas = {a['area_code']: a['area_id'] for a in db.get_mine_areas()}
    
    sources = [
        # Klein Dwars River Boreholes (6)
        {
            'source_code': 'KDB1', 'source_name': 'Klein Dwars Borehole 1',
            'type_id': types['BH'], 'area_id': None,
            'description': 'Borehole on Klein Dwars River catchment',
            'authorized_volume': 6000, 'authorization_period': 'annual',
            'river_name': 'Klein Dwars River', 'active': 1
        },
        {
            'source_code': 'KDB2', 'source_name': 'Klein Dwars Borehole 2',
            'type_id': types['BH'], 'area_id': None,
            'description': 'Borehole on Klein Dwars River catchment',
            'river_name': 'Klein Dwars River', 'active': 1
        },
        {
            'source_code': 'KDB3', 'source_name': 'Klein Dwars Borehole 3',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Klein Dwars River', 'active': 1
        },
        {
            'source_code': 'KDB4', 'source_name': 'Klein Dwars Borehole 4',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Klein Dwars River', 'active': 1
        },
        {
            'source_code': 'KDB5', 'source_name': 'Klein Dwars Borehole 5',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Klein Dwars River', 'active': 1
        },
        {
            'source_code': 'KDB6', 'source_name': 'Klein Dwars Borehole 6',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Klein Dwars River', 'active': 1
        },
        
        # Groot Dwars River Boreholes (6)
        {
            'source_code': 'GDB1', 'source_name': 'Groot Dwars Borehole 1',
            'type_id': types['BH'], 'area_id': None,
            'description': 'Borehole on Groot Dwars River catchment',
            'river_name': 'Groot Dwars River', 'active': 1
        },
        {
            'source_code': 'GDB2', 'source_name': 'Groot Dwars Borehole 2',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Groot Dwars River', 'active': 1
        },
        {
            'source_code': 'GDB3', 'source_name': 'Groot Dwars Borehole 3',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Groot Dwars River', 'active': 1
        },
        {
            'source_code': 'GDB4', 'source_name': 'Groot Dwars Borehole 4',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Groot Dwars River', 'active': 1
        },
        {
            'source_code': 'GDB5', 'source_name': 'Groot Dwars Borehole 5',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Groot Dwars River', 'active': 1
        },
        {
            'source_code': 'GDB6', 'source_name': 'Groot Dwars Borehole 6',
            'type_id': types['BH'], 'area_id': None,
            'river_name': 'Groot Dwars River', 'active': 1
        },
        
        # Rivers (2)
        {
            'source_code': 'KD', 'source_name': 'Klein Dwars River',
            'type_id': types['RIVER'], 'area_id': None,
            'description': 'Klein Dwars River surface water abstraction via Inyoni Dam',
            'authorized_volume': 89167, 'authorization_period': 'monthly',
            'max_flow_rate': 2972, 'river_name': 'Klein Dwars River',
            'active': 1
        },
        {
            'source_code': 'GD', 'source_name': 'Groot Dwars River',
            'type_id': types['RIVER'], 'area_id': None,
            'description': 'Groot Dwars River surface water abstraction via De Brochen Dam',
            'authorized_volume': 550000, 'authorization_period': 'monthly',
            'max_flow_rate': 18333, 'river_name': 'Groot Dwars River',
            'active': 1
        },
        
        # Underground Abstractions (4)
        {
            'source_code': 'NDUGW', 'source_name': 'North Decline Underground Water',
            'type_id': types['UG'], 'area_id': areas['UG2N'],
            'description': 'UG2 North Decline underground dewatering',
            'authorized_volume': 390.6, 'authorization_period': 'daily',
            'active': 1
        },
        {
            'source_code': 'SDUGW', 'source_name': 'South Decline Underground Water',
            'type_id': types['UG'], 'area_id': areas['UG2S'],
            'description': 'UG2 South Decline underground dewatering',
            'authorized_volume': 1554, 'authorization_period': 'daily',
            'active': 1
        },
        {
            'source_code': 'MNUGW', 'source_name': 'Merensky North Underground Water',
            'type_id': types['UG'], 'area_id': areas['MERN'],
            'description': 'Merensky North Decline underground dewatering',
            'active': 1
        },
        {
            'source_code': 'MSUGW', 'source_name': 'Merensky South Underground Water',
            'type_id': types['UG'], 'area_id': areas['MERM'],
            'description': 'Merensky Main Decline underground dewatering',
            'active': 1
        },
    ]
    
    for source in sources:
        try:
            source_id = db.add_water_source(source)
            print(f"  ✅ Added: {source['source_code']} - {source['source_name']}")
        except Exception as e:
            print(f"  ❌ Error adding {source['source_code']}: {e}")
    
    print(f"  Total sources added: {len(sources)}")


def populate_storage_facilities(db: DatabaseManager):
    """Add all 10 storage facilities from analysis"""
    
    print("\n🏊 Adding Storage Facilities...")
    
    areas = {a['area_code']: a['area_id'] for a in db.get_mine_areas()}
    
    facilities = [
        {
            'facility_code': 'INYONI',
            'facility_name': 'Inyoni Dam',
            'facility_type': 'dam',
            'area_id': None,
            'total_capacity': 500000,  # 0.5 Mm³ = 500,000 m³
            'surface_area': 50000,  # Estimated
            'purpose': 'raw_water',
            'water_quality': 'process',
            'description': 'Klein Dwars River storage for UG2 plant supply',
            'commissioned_date': '2010-01-01',
            'active': 1
        },
        {
            'facility_code': 'DEBROCHEN',
            'facility_name': 'De Brochen Dam',
            'facility_type': 'dam',
            'area_id': None,
            'total_capacity': 9020000,  # 9.02 Mm³
            'surface_area': 500000,  # Estimated
            'purpose': 'raw_water',
            'water_quality': 'process',
            'description': 'Groot Dwars River storage for plant supply',
            'commissioned_date': '2010-01-01',
            'active': 1
        },
        {
            'facility_code': 'PLANT_RWD',
            'facility_name': 'Plant Return Water Dam',
            'facility_type': 'dam',
            'area_id': None,
            'total_capacity': 100000,  # Estimated
            'surface_area': 10000,
            'purpose': 'return_water',
            'water_quality': 'process',
            'description': 'Return water storage for plant recycle',
            'active': 1
        },
        {
            'facility_code': 'OLD_TSF',
            'facility_name': 'Old Tailings Storage Facility',
            'facility_type': 'dam',
            'area_id': None,
            'total_capacity': 1000000,  # Estimated
            'surface_area': 100000,
            'purpose': 'return_water',
            'water_quality': 'process',
            'description': 'Old TSF with return water collection',
            'siltation_percentage': 20.0,
            'active': 1
        },
        {
            'facility_code': 'NEW_TSF',
            'facility_name': 'New Tailings Storage Facility',
            'facility_type': 'dam',
            'area_id': None,
            'total_capacity': 3091872,  # Authorized disposal volume (annual)
            'surface_area': 200000,
            'purpose': 'return_water',
            'water_quality': 'process',
            'description': 'New TSF for expanded operations',
            'active': 1
        },
        {
            'facility_code': 'NDCD1-4',
            'facility_name': 'North Decline Clean Dams 1-4',
            'facility_type': 'dam',
            'area_id': areas['UG2N'],
            'total_capacity': 92184,  # From Excel analysis
            'surface_area': 5000,
            'purpose': 'clean_water',
            'water_quality': 'process',
            'description': 'North decline clean water storage',
            'pump_start_level': 70.0,
            'pump_stop_level': 50.0,
            'active': 1
        },
        {
            'facility_code': 'NDSWD1-2',
            'facility_name': 'North Decline Storm Water Dams 1-2',
            'facility_type': 'dam',
            'area_id': areas['UG2N'],
            'total_capacity': 50000,  # Estimated
            'surface_area': 3000,
            'purpose': 'storm_water',
            'water_quality': 'process',
            'description': 'North decline stormwater collection',
            'active': 1
        },
        {
            'facility_code': 'SPCD1',
            'facility_name': 'Stockpile Clean Dam 1',
            'facility_type': 'dam',
            'area_id': None,
            'total_capacity': 30000,  # Estimated
            'surface_area': 2000,
            'purpose': 'storm_water',
            'water_quality': 'process',
            'description': 'Stockpile area stormwater collection',
            'active': 1
        },
        {
            'facility_code': 'MDCD5-6',
            'facility_name': 'Merensky Decline Clean Dams 5-6',
            'facility_type': 'dam',
            'area_id': areas['MERN'],
            'total_capacity': 40000,  # Estimated
            'surface_area': 2500,
            'purpose': 'clean_water',
            'water_quality': 'process',
            'description': 'Merensky decline clean water storage',
            'pump_start_level': 70.0,
            'pump_stop_level': 30.0,
            'active': 1
        },
        {
            'facility_code': 'MDSWD3-4',
            'facility_name': 'Merensky Decline Storm Water Dams 3-4',
            'facility_type': 'dam',
            'area_id': areas['MERN'],
            'total_capacity': 35000,  # Estimated
            'surface_area': 2000,
            'purpose': 'storm_water',
            'water_quality': 'process',
            'description': 'Merensky decline stormwater collection',
            'active': 1
        },
    ]
    
    for facility in facilities:
        try:
            facility_id = db.add_storage_facility(facility)
            print(f"  ✅ Added: {facility['facility_code']} - {facility['facility_name']}")
        except Exception as e:
            print(f"  ❌ Error adding {facility['facility_code']}: {e}")
    
    print(f"  Total facilities added: {len(facilities)}")
    
    # Calculate total capacity
    total_capacity = sum(f['total_capacity'] for f in facilities)
    print(f"  📊 Total storage capacity: {total_capacity:,.0f} m³ ({total_capacity/1000000:.2f} Mm³)")


def main():
    """Populate database with TRP water balance data"""
    print("=" * 70)
    print("POPULATING DATABASE WITH TRP WATER BALANCE DATA")
    print("=" * 70)
    
    db = DatabaseManager()
    
    # Populate water sources
    populate_water_sources(db)
    
    # Populate storage facilities
    populate_storage_facilities(db)
    
    # Display summary
    print("\n" + "=" * 70)
    print("DATABASE POPULATION COMPLETE")
    print("=" * 70)
    
    stats = db.get_dashboard_stats()
    print(f"\n📊 Database Summary:")
    print(f"  • Water Sources: {stats['total_sources']}")
    print(f"  • Storage Facilities: {stats['total_facilities']}")
    print(f"  • Total Storage Capacity: {stats['total_capacity']:,.0f} m³")
    print(f"  • Mine Areas: {len(db.get_mine_areas())}")
    print(f"  • Source Types: {len(db.get_water_source_types())}")
    print(f"  • System Constants: {len(db.get_all_constants())}")
    
    print("\n✅ Database ready for use!")
    print(f"   Location: {db.db_path}")


if __name__ == "__main__":
    main()
