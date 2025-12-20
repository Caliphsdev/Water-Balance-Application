import json

# Load as binary and fix the byte corruption
with open('data/diagrams/ug2_north_decline.json', 'rb') as f:
    content = f.read()

# The corrupted arrow bytes
corrupted = b'\xc3\xa2\xe2\x80\xa0\xe2\x80\x99'
proper = '→'.encode('utf-8')

print(f'Corrupted bytes: {corrupted}')
print(f'Proper arrow bytes: {proper}')

# Replace
fixed_content = content.replace(corrupted, proper)

# Count fixes
count = content.count(corrupted)
print(f'Fixed {count} corrupted arrows')

# Save
with open('data/diagrams/ug2_north_decline.json', 'wb') as f:
    f.write(fixed_content)

# Verify
data = json.loads(fixed_content.decode('utf-8'))
edges = [e for e in data.get('edges', []) if e.get('excel_mapping', {}).get('enabled')]
if edges:
    sample = edges[0].get('excel_mapping', {}).get('column', '')
    print(f'Sample column: {sample}')
    print(f'Contains proper →: {"→" in sample}')
