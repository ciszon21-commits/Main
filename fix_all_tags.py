#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix all multi-line template tags in user_edit_form.html"""

import re

# Read the file
with open('EngineerRPG/templates/EngineerRPG/user_edit_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all multi-line template tags by joining lines
# Pattern 1: Fix the is_active checkbox tag
content = re.sub(
    r'{% if user_profile\.user\.is_active\s+%}checked{% endif %}',
    '{% if user_profile.user.is_active %}checked{% endif %}',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Pattern 2: Fix any remaining split tags with ==
content = re.sub(
    r'{% if ([^%]+)==([^%]+)\s+%}',
    r'{% if \1 == \2 %}',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Pattern 3: Fix any remaining split tags
content = re.sub(
    r'{% if ([^%]+)\s+%}',
    r'{% if \1 %}',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Write the fixed content back
with open('EngineerRPG/templates/EngineerRPG/user_edit_form.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("File fixed successfully!")
print("All multi-line template tags have been merged into single lines")
