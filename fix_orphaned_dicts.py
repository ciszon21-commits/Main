import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = []

# Fix orphaned dict entries (lines that start with 'error': or 'success': without return JsonResponse)
for i, line in enumerate(lines, 1):
    original = line
    stripped = line.lstrip()
    
    # Check if line is an orphaned dict entry
    if (stripped.startswith("'error':") or stripped.startswith("'success':") or 
        stripped.startswith("'message':")) and 'return' not in line:
        # Check if previous line doesn't have return JsonResponse
        if i > 1 and 'return JsonResponse' not in lines[i-2]:
            indent = len(line) - len(line.lstrip())
            
            # Replace with proper return statement
            if "'error':" in line:
                lines[i-1] = ' ' * indent + "return JsonResponse({'error': 'An error occurred'}, status=400)\r\n"
                changes.append(f"Line {i}: Fixed orphaned error dict")
            elif "'success':" in line:
                lines[i-1] = ' ' * indent + "return JsonResponse({'success': True})\r\n"
                changes.append(f"Line {i}: Fixed orphaned success dict")
            elif "'message':" in line:
                lines[i-1] = ' ' * indent + "return JsonResponse({'message': 'Operation completed'})\r\n"
                changes.append(f"Line {i}: Fixed orphaned message dict")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Fixed {len(changes)} orphaned dict entries")
for change in changes:
    print(f"  {change}")
