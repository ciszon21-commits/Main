#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check and display the template file around line 104"""

with open('EngineerRPG/templates/EngineerRPG/user_edit_form.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("\nLines 100-110:")
for i in range(99, min(110, len(lines))):
    print(f"Line {i+1}: {lines[i].rstrip()}")

# Check for misplaced endif
for i, line in enumerate(lines, 1):
    if '{% endif %}' in line and i > 100:
        print(f"\nFound {% endif %} at line {i}: {line.strip()}")
