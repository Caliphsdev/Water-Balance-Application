from src.database.db_manager import DatabaseManager

db = DatabaseManager()

print("=== WB_INFLOW_SOURCES STRUCTURE ===")
result = db.execute_query("PRAGMA table_info(wb_inflow_sources)")
for row in result:
    print(f"  {row['name']}: {row['type']}")

print("\n=== SAMPLE DATA ===")
result = db.execute_query("SELECT * FROM wb_inflow_sources LIMIT 5")
for row in result:
    print(f"  {dict(row)}")
