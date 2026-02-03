import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Scan for nested returns
potential_issues = []
for i, line in enumerate(lines):
    if 'return JsonResponse({' in line:
        # Check next few lines for another return JsonResponse
        for j in range(1, 10): # Look ahead 10 lines
            if i + j < len(lines):
                next_line = lines[i+j]
                if 'return JsonResponse' in next_line:
                    potential_issues.append((i, i+j))
                    break

print(f"Found {len(potential_issues)} nested return blocks:")
for start, inner in potential_issues:
    print(f"  Outer at line {start+1}, Inner at line {inner+1}")
    print(f"  Content scan:")
    for k in range(start, inner+2):
        print(f"    {lines[k].strip()}")
    print("-" * 20)

# If we want to fix them, we can do it here too
if potential_issues:
    # Process in reverse order to keep indices valid
    for start, inner in reversed(potential_issues):
        # Find the closing brace line
        end = -1
        for k in range(inner, inner + 10):
            if k < len(lines) and '}, status=' in lines[k]:
                end = k
                break
        
        if end != -1:
            print(f"Fixing block lines {start+1}-{end+1}")
            # Delete block
            del lines[start:end+1]
            # Insert replacement
            lines.insert(start, "                        return JsonResponse({'error': 'An error occurred'}, status=400)\r\n")
        else:
            print(f"Could not find closing brace for block starting at {start+1}")

    # Write back
    with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Applied fixes.")
