"""Script to update all inter-area transfers to include is_bidirectional column."""
from pathlib import Path

file_path = Path(__file__).parents[1] / "src" / "database" / "migrate_wb_schema.py"
content = file_path.read_text(encoding='utf-8')

# Step 1: Replace INSERT column list
old_insert = 'INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, notes)'
new_insert = 'INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)'
content = content.replace(old_insert, new_insert)

# Step 2: Add is_bidirectional=1 to all VALUES lines with dirty flows
lines = content.split('\n')
for i, line in enumerate(lines):
    # Find VALUES lines for inter_area_transfers with 'dirty'
    if '"dirty",' in line and 'area_id,' in line and line.strip().startswith('('):
        # Insert ', 1' before the last parameter (notes string)
        parts = line.rsplit(',', 1)
        if len(parts) == 2 and parts[1].strip().startswith('"'):
            lines[i] = parts[0] + ', 1,' + parts[1]

content = '\n'.join(lines)
file_path.write_text(content, encoding='utf-8')
print("✅ Updated all inter-area transfers with is_bidirectional=1 for dirty flows")
