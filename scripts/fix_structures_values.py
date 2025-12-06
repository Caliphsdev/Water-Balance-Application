"""Fix VALUES placeholders for wb_structures (should be 7, not 8)."""
from pathlib import Path

file_path = Path(__file__).parents[1] / "src" / "database" / "migrate_wb_schema.py"
content = file_path.read_text(encoding='utf-8')

# Fix wb_structures VALUES from 8 to 7 placeholders
content = content.replace(
    'wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"\n                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    'wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"\n                " VALUES (?, ?, ?, ?, ?, ?, ?)'
)

file_path.write_text(content, encoding='utf-8')
print("✅ Fixed wb_structures VALUES placeholders to 7 parameters")
