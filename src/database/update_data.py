"""
Update existing data with flow rates and operating levels
"""

import sqlite3
from pathlib import Path

def update_existing_data():
    """Update existing water sources and storage facilities with additional data"""
    
    db_path = Path(__file__).parent.parent.parent / 'data' / 'water_balance.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("Updating existing data...")
        
        # Update water sources with average flow rates based on analysis
        updates = [
            ('KD', 89167.33, 'm³/month', 0.8),  # Klein Dwars River
            ('GD', 550000, 'm³/month', 0.9),    # Groot Dwars River
            ('KDB1', 5000, 'm³/month', 0.85),
            ('KDB2', 5000, 'm³/month', 0.85),
            ('KDB3', 5000, 'm³/month', 0.85),
            ('KDB4', 5000, 'm³/month', 0.85),
            ('KDB5', 5000, 'm³/month', 0.85),
            ('KDB6', 5000, 'm³/month', 0.85),
            ('GDB1', 8000, 'm³/month', 0.9),
            ('GDB2', 8000, 'm³/month', 0.9),
            ('GDB3', 8000, 'm³/month', 0.9),
            ('GDB4', 8000, 'm³/month', 0.9),
            ('GDB5', 8000, 'm³/month', 0.9),
            ('GDB6', 8000, 'm³/month', 0.9),
            ('NDUGW', 15000, 'm³/month', 0.95),  # North Decline Underground Water
            ('SDUGW', 12000, 'm³/month', 0.95),  # South Decline Underground Water
            ('MNUGW', 10000, 'm³/month', 0.9),   # Merensky North Underground Water
            ('MSUGW', 10000, 'm³/month', 0.9),   # Merensky South Underground Water
        ]
        
        for source_code, avg_flow, units, reliability in updates:
            cursor.execute("""
                UPDATE water_sources 
                SET average_flow_rate = ?, 
                    flow_units = ?,
                    reliability_factor = ?
                WHERE source_code = ?
            """, (avg_flow, units, reliability, source_code))
            print(f"  Updated {source_code}: {avg_flow:,.0f} {units}, reliability {reliability*100:.0f}%")
        
        # Update storage facilities with operating levels (as percentages)
        facility_updates = [
            ('INYONI', 20),           # Inyoni Dam - estimated max depth
            ('DEBROCHEN', 15),        # Debrochen Dam
            ('PLANT_RWD', 30),        # Plant Return Water Dam
            ('OLD_TSF', 10),          # Old TSF
            ('NEW_TSF', 10),          # New TSF
            ('NDCD1', 25),            # North Decline Clean Dam 1
            ('NDCD2', 25),            # North Decline Clean Dam 2
            ('NDCD3', 25),            # North Decline Clean Dam 3
            ('NDCD4', 25),            # North Decline Clean Dam 4
            ('NDSWD1', 20),           # North Decline Slimes Water Dam 1
            ('NDSWD2', 20),           # North Decline Slimes Water Dam 2
            ('SPCD1', 25),            # Sandsloot Pit Clean Dam 1
            ('MDCD5', 25),            # Merensky Decline Clean Dam 5
            ('MDCD6', 45.0),          # Merensky Decline Clean Dam 6
            ('MDSWD3', 32.0),         # Merensky Decline Slimes Water Dam 3
            ('MDSWD4', 32.0),         # Merensky Decline Slimes Water Dam 4
        ]
        
        for fac_code, max_depth in facility_updates:
            cursor.execute("""
                UPDATE storage_facilities 
                SET max_depth = ?
                WHERE facility_code = ?
            """, (max_depth, fac_code))
            print(f"  Updated {fac_code}: max_depth {max_depth}m")
        
        conn.commit()
        print("\n✅ Data update completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Update failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    update_existing_data()
