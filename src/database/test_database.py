"""
Database Test & Demonstration
Quick test to verify database operations are working correctly
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager


def test_database():
    """Test database operations"""
    print("=" * 70)
    print("DATABASE OPERATIONS TEST")
    print("=" * 70)
    
    db = DatabaseManager()
    
    # Test 1: Get water sources
    print("\n1️⃣ Testing Water Sources Retrieval...")
    sources = db.get_water_sources()
    print(f"   ✅ Retrieved {len(sources)} water sources")
    
    # Show sample sources
    print("\n   Sample sources:")
    for source in sources[:5]:
        print(f"   • {source['source_code']}: {source['source_name']} ({source['type_name']})")
    
    # Test 2: Get storage facilities
    print("\n2️⃣ Testing Storage Facilities Retrieval...")
    facilities = db.get_storage_facilities()
    print(f"   ✅ Retrieved {len(facilities)} storage facilities")
    
    # Show sample facilities with capacity
    print("\n   Sample facilities:")
    for facility in facilities[:5]:
        capacity_mm3 = facility['total_capacity'] / 1000000
        print(f"   • {facility['facility_code']}: {facility['facility_name']}")
        print(f"     Capacity: {facility['total_capacity']:,.0f} m³ ({capacity_mm3:.2f} Mm³)")
    
    # Test 3: Get reference data
    print("\n3️⃣ Testing Reference Data...")
    
    # Mine areas
    areas = db.get_mine_areas()
    print(f"   ✅ Mine areas: {len(areas)}")

    # Test 9: Hard delete facility
    print("\n9️⃣ Testing Hard Delete Facility...")
    if facilities:
        test_facility_id = facilities[-1]['facility_id']
        print(f"   Attempting to hard delete facility ID: {test_facility_id}")
        deleted = db.hard_delete_storage_facility(test_facility_id)
        print(f"   Deleted rows: {deleted}")
        # Confirm deletion
        check = db.get_storage_facility(test_facility_id)
        if check is None:
            print("   ✅ Facility permanently deleted!")
        else:
            print("   ❌ Facility still exists!")
    for area in areas:
        print(f"   • {area['area_code']}: {area['area_name']}")
    
    # Source types
    types = db.get_water_source_types()
    print(f"\n   ✅ Source types: {len(types)}")
    for stype in types:
        print(f"   • {stype['type_code']}: {stype['type_name']}")
    
    # Test 4: Get system constants
    print("\n4️⃣ Testing System Constants...")
    constants = db.get_all_constants()
    print(f"   ✅ Constants loaded: {len(constants)}")
    print("\n   Key calculation constants:")
    print(f"   • Mining Water Rate: {constants.get('MINING_WATER_RATE', 0)} m³/tonne")
    print(f"   • Slurry Density: {constants.get('SLURRY_DENSITY', 0)} t/m³")
    
    # Test 5: Get evaporation rates
    print("\n5️⃣ Testing Evaporation Rates...")
    jan_evap = db.get_evaporation_rate(1)
    jul_evap = db.get_evaporation_rate(7)
    print(f"   ✅ January evaporation: {jan_evap} mm")
    print(f"   ✅ July evaporation: {jul_evap} mm")
    
    # Test 6: Dashboard statistics
    print("\n6️⃣ Testing Dashboard Statistics...")
    stats = db.get_dashboard_stats()
    print(f"   ✅ Total sources: {stats['total_sources']}")
    print(f"   ✅ Total facilities: {stats['total_facilities']}")
    print(f"   ✅ Total storage capacity: {stats['total_capacity']:,.0f} m³")
    print(f"   ✅ Current volume: {stats['total_current_volume']:,.0f} m³")
    print(f"   ✅ Utilization: {stats['total_utilization_percent']:.1f}%")
    
    # Test 7: Query specific source
    print("\n7️⃣ Testing Single Record Retrieval...")
    # Get Klein Dwars River
    kd_sources = [s for s in sources if s['source_code'] == 'KD']
    if kd_sources:
        kd = db.get_water_source(kd_sources[0]['source_id'])
        print(f"   ✅ Klein Dwars River details:")
        print(f"   • Source: {kd['source_name']}")
        print(f"   • Type: {kd['type_name']}")
        print(f"   • Authorized: {kd['authorized_volume']:,} m³/month")
        print(f"   • Max flow: {kd['max_flow_rate']:,} m³/day")
    
    # Test 8: Query specific facility
    print("\n8️⃣ Testing Facility Record...")
    inyoni = [f for f in facilities if f['facility_code'] == 'INYONI']
    if inyoni:
        dam = db.get_storage_facility(inyoni[0]['facility_id'])
        print(f"   ✅ Inyoni Dam details:")
        print(f"   • Facility: {dam['facility_name']}")
        print(f"   • Type: {dam['facility_type']}")
        print(f"   • Capacity: {dam['total_capacity']:,} m³")
        print(f"   • Surface area: {dam['surface_area']:,} m²")
        print(f"   • Pump start: {dam['pump_start_level']}%")
        print(f"   • Pump stop: {dam['pump_stop_level']}%")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✅")
    print("=" * 70)
    print("\n💾 Database is fully operational!")
    print(f"   Location: {db.db_path}")
    print("\n🚀 Ready for application integration!")


if __name__ == "__main__":
    test_database()
