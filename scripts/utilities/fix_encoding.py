import json

# Load with proper encoding
with open('data/diagrams/ug2_north_decline.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix corrupted arrows
# The arrow → was encoded as UTF-8 bytes and then read as Latin-1
# This creates the corrupted sequence
corrupted_patterns = [
    'Ã¢â€ â€™',  # Common corruption of →
]

for pattern in corrupted_patterns:
    content = content.replace(pattern, '→')

# Save with proper encoding
with open('data/diagrams/ug2_north_decline.json', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed encoding corruption')

# Verify
data = json.loads(content)
edges = [e for e in data.get('edges', []) if e.get('excel_mapping', {}).get('enabled')]
sample = edges[0].get('excel_mapping', {}).get('column', '')
print(f'Sample column: {sample}')
print(f'Contains →: {"→" in sample}')
