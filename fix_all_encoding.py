import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = []

# Fix unterminated strings with garbled characters
for i, line in enumerate(lines, 1):
    original = line
    
    # Fix messages with garbled characters - look for patterns like messages.xxx(request, '...')
    # where the string contains non-ASCII and isn't properly terminated
    if 'messages.' in line and "'" in line:
        # Check if line has unterminated string (odd number of quotes after messages)
        msg_start = line.find('messages.')
        if msg_start != -1:
            after_msg = line[msg_start:]
            # Count quotes
            single_quotes = after_msg.count("'")
            if single_quotes % 2 != 0:  # Odd number means unterminated
                # Replace the entire message call with a generic one
                indent = len(line) - len(line.lstrip())
                if 'success' in line:
                    lines[i-1] = ' ' * indent + "messages.success(request, 'Operation successful')\r\n"
                elif 'error' in line:
                    lines[i-1] = ' ' * indent + "messages.error(request, 'An error occurred')\r\n"
                elif 'warning' in line:
                    lines[i-1] = ' ' * indent + "messages.warning(request, 'Warning')\r\n"
                
                if lines[i-1] != original:
                    changes.append(f"Line {i}: Fixed unterminated string")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Fixed {len(changes)} lines")
for change in changes[:20]:  # Show first 20
    print(f"  {change}")
if len(changes) > 20:
    print(f"  ... and {len(changes) - 20} more")
