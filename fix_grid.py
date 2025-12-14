#!/usr/bin/env python3
import re

# Read file
with open('src/ui/flow_diagram_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Process lines to remove the Show Grid button
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this is the start of the Show Grid button
    if "Button(button_frame, text='📐 Show Grid'" in line:
        # Skip this line and the next line (which has the closing part)
        i += 1
        if i < len(lines) and ".pack(side='left', padx=5)" in lines[i]:
            i += 1
        continue
    new_lines.append(line)
    i += 1

# Write back
with open('src/ui/flow_diagram_dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ Show Grid button removed')
