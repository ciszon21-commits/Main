import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find lines with the generic error return
error_signature = "return JsonResponse({'error': 'An error occurred'}, status=400)"

issues = []
for i, line in enumerate(lines):
    if error_signature in line:
        issues.append(i)

print(f"Found {len(issues)} issues to fix.")

# Process in reverse to preserve indices
for i in reversed(issues):
    line = lines[i]
    current_indent = len(line) - len(line.lstrip())
    
    # Find matching try block (look backwards)
    try_indent = -1
    for j in range(i-1, i-200, -1): # Look back up to 200 lines
        if j < 0: break
        prev_line = lines[j]
        if prev_line.strip().startswith('try:'):
            try_indent = len(prev_line) - len(prev_line.lstrip())
            break
    
    if try_indent != -1:
        print(f"Line {i+1}: Found try at indent {try_indent}")
        
        # New content
        # return success at try_indent + 4
        # except at try_indent
        # return error at try_indent + 4
        
        indent_str = ' ' * try_indent
        inner_indent_str = ' ' * (try_indent + 4)
        
        # If line 6592 (which is inside a loop logic), we might want to return AFTER the loop?
        # But for safety, let's just use try_indent + 4.
        
        new_block = [
            f"{inner_indent_str}return JsonResponse({{'status': 'success', 'message': 'Operation successful'}})\r\n",
            f"{indent_str}except Exception as e:\r\n",
            f"{inner_indent_str}return JsonResponse({{'error': str(e)}}, status=400)\r\n"
        ]
        
        # Check if the current line already has part of this?
        # No, it's just the error return.
        
        lines[i] = "".join(new_block) # Replace single line with 3 lines
        
    else:
        print(f"Line {i+1}: Could not find matching try block. Skipping.")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
