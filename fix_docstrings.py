import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = []

# Fix docstrings with garbled characters
for i, line in enumerate(lines, 1):
    original = line
    
    # Check if line is a docstring (starts with """ after whitespace)
    stripped = line.lstrip()
    if stripped.startswith('"""') or stripped.startswith("'''"):
        # Check for garbled characters or unterminated strings
        has_garbled = any(ord(c) > 127 and ord(c) not in range(0x4E00, 0x9FFF) for c in line)
        
        # Check if docstring is properly terminated on same line
        quote_type = '"""' if '"""' in stripped else "'''"
        if has_garbled or (line.count(quote_type) == 1):  # Only opening quote
            indent = len(line) - len(line.lstrip())
            lines[i-1] = ' ' * indent + '"""Function docstring"""\r\n'
            changes.append(f"Line {i}: Fixed docstring")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Fixed {len(changes)} docstrings")
for change in changes[:30]:
    print(f"  {change}")
if len(changes) > 30:
    print(f"  ... and {len(changes) - 30} more")
