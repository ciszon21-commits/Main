#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix the user_edit_form.html template file"""

import re

# Read the file
with open('EngineerRPG/templates/EngineerRPG/user_edit_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the split template tag on lines 79-80
# Replace the multi-line if statement with a single-line version
content = re.sub(
    r'<option value="\{\{ char_class\.id \}\}" \{% if char_class\.id==user_profile\.character_class\.id\s+%\}selected\{% endif %\}>',
    '<option value="{{ char_class.id }}" {% if char_class.id == user_profile.character_class.id %}selected{% endif %}>',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Also add spaces around == operator
content = content.replace('char_class.id==user_profile', 'char_class.id == user_profile')
content = content.replace('value==user_profile', 'value == user_profile')

# Write the fixed content back
with open('EngineerRPG/templates/EngineerRPG/user_edit_form.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("File fixed successfully!")
print("Fixed issues:")
print("1. Merged split template tags into single lines")
print("2. Added spaces around == operators")
