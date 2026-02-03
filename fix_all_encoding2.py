import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = []

# Fix unterminated strings with garbled characters - more aggressive approach
for i, line in enumerate(lines, 1):
    original = line
    
    # Fix messages.info/success/error/warning with garbled characters
    if 'messages.' in line:
        # Check for unterminated strings - look for patterns with odd quotes
        # or non-printable characters
        has_garbled = any(ord(c) > 127 and ord(c) not in range(0x4E00, 0x9FFF) for c in line)
        
        if has_garbled or (line.count("'") % 2 != 0 and 'messages.' in line):
            indent = len(line) - len(line.lstrip())
            
            if 'messages.success' in line:
                lines[i-1] = ' ' * indent + "messages.success(request, 'Operation successful')\r\n"
                changes.append(f"Line {i}: Fixed messages.success")
            elif 'messages.error' in line:
                lines[i-1] = ' ' * indent + "messages.error(request, 'An error occurred')\r\n"
                changes.append(f"Line {i}: Fixed messages.error")
            elif 'messages.warning' in line:
                lines[i-1] = ' ' * indent + "messages.warning(request, 'Warning')\r\n"
                changes.append(f"Line {i}: Fixed messages.warning")
            elif 'messages.info' in line:
                lines[i-1] = ' ' * indent + "messages.info(request, 'Information')\r\n"
                changes.append(f"Line {i}: Fixed messages.info")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Fixed {len(changes)} lines")
for change in changes[:30]:  # Show first 30
    print(f"  {change}")
if len(changes) > 30:
    print(f"  ... and {len(changes) - 30} more")
