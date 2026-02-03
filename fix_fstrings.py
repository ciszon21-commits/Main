import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = []

# Fix f-strings and dictionary values with garbled characters
for i, line in enumerate(lines, 1):
    original = line
    
    # Check if line contains f-string or dictionary value with garbled characters
    if ("f'" in line or "f\"" in line or "'error':" in line or "'success':" in line or "'message':" in line):
        # Check for garbled characters (non-ASCII, non-CJK)
        has_garbled = any(ord(c) > 127 and ord(c) not in range(0x4E00, 0x9FFF) for c in line)
        
        if has_garbled or (line.count("'") % 2 != 0 and ("f'" in line or "'error':" in line)):
            indent = len(line) - len(line.lstrip())
            
            # Fix dictionary error/success/message values
            if "'error':" in line or "'message':" in line:
                lines[i-1] = ' ' * indent + "'error': 'An error occurred',\r\n"
                changes.append(f"Line {i}: Fixed dict error value")
            elif "'success':" in line:
                lines[i-1] = ' ' * indent + "'success': True,\r\n"
                changes.append(f"Line {i}: Fixed dict success value")
            # Fix f-strings
            elif "f'" in line or "f\"" in line:
                # Replace with simple string
                if 'return JsonResponse' in lines[i-2] if i > 1 else False:
                    lines[i-1] = ' ' * indent + "'error': 'Invalid operation'\r\n"
                else:
                    lines[i-1] = ' ' * indent + "# Fixed garbled f-string\r\n"
                changes.append(f"Line {i}: Fixed f-string")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Fixed {len(changes)} lines")
for change in changes[:30]:
    print(f"  {change}")
if len(changes) > 30:
    print(f"  ... and {len(changes) - 30} more")
