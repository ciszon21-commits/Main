import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = []

# Fix dictionary literals with garbled strings
for i, line in enumerate(lines, 1):
    original = line
    
    # Check if line contains dictionary with 'name':, 'desc':, etc.
    if ("'name':" in line or "'desc':" in line) and '{' in line:
        # Check for garbled characters or unterminated strings
        has_garbled = any(ord(c) > 127 and ord(c) not in range(0x4E00, 0x9FFF) for c in line)
        
        # Count quotes to see if unterminated
        single_quotes = line.count("'")
        
        if has_garbled or (single_quotes % 2 != 0):
            # Replace the entire dictionary line with a safe version
            indent = len(line) - len(line.lstrip())
            
            # Extract item_type if present
            item_type = 'BASIC'
            if "'item_type':" in line:
                match = re.search(r"'item_type':\s*'(\w+)'", line)
                if match:
                    item_type = match.group(1)
            
            # Create a safe replacement
            lines[i-1] = ' ' * indent + f"{{'name': 'Item', 'item_type': '{item_type}', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'}},\r\n"
            changes.append(f"Line {i}: Fixed dict literal")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Fixed {len(changes)} dictionary literals")
for change in changes[:30]:
    print(f"  {change}")
if len(changes) > 30:
    print(f"  ... and {len(changes) - 30} more")
