#!/usr/bin/env python3

# Read file
with open('src/ui/flow_diagram_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the info text to reflect grid is always on
old_text = 'DRAG COMPONENTS to move | SELECT + "Lock/Unlock" to lock position | GRID: Snap when moving, Show for alignment'
new_text = 'DRAG COMPONENTS to move | SELECT + "Lock/Unlock" to lock position | GRID: Always visible (20px intervals)'

content = content.replace(old_text, new_text)

# Write back
with open('src/ui/flow_diagram_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Info text updated - Grid always visible')
