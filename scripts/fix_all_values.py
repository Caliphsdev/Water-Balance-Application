"""Fix VALUES placeholders for all tables except wb_inter_area_transfers."""
from pathlib import Path

file_path = Path(__file__).parents[1] / "src" / "database" / "migrate_wb_schema.py"
content = file_path.read_text(encoding='utf-8')

# Fix wb_flow_connections (7 params)
content = content.replace(
    'wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"\n                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    'wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"\n                " VALUES (?, ?, ?, ?, ?, ?, ?)'
)

# Fix wb_inflow_sources (5 params)
content = content.replace(
    'wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"\n                " VALUES (?, ?, ?, ?, ?, ?)',
    'wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"\n                " VALUES (?, ?, ?, ?, ?)'
)

# Fix wb_outflow_destinations (5 params)
content = content.replace(
    'wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"\n                " VALUES (?, ?, ?, ?, ?, ?)',
    'wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"\n                " VALUES (?, ?, ?, ?, ?)'
)

file_path.write_text(content, encoding='utf-8')
print("✅ Fixed all VALUES placeholders to match column counts")
