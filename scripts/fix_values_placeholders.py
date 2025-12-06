"""Update VALUES placeholders for inter_area_transfers."""
from pathlib import Path

file_path = Path(__file__).parents[1] / "src" / "database" / "migrate_wb_schema.py"
content = file_path.read_text(encoding='utf-8')

# Replace VALUES (?, ?, ?, ?, ?, ?, ?) with VALUES (?, ?, ?, ?, ?, ?, ?, ?)
# for lines that have is_bidirectional in column list
content = content.replace('" VALUES (?, ?, ?, ?, ?, ?, ?)"', '" VALUES (?, ?, ?, ?, ?, ?, ?, ?)"')

file_path.write_text(content, encoding='utf-8')
print("✅ Updated VALUES placeholders to include is_bidirectional parameter")
