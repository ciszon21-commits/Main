import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix 1: node.id in parent_ids (around line 7005 in view)
# Look for: if node.id in parent_ids:
# Then find the "An error occurred" return and replace it.

for i in range(len(lines)):
    line = lines[i].strip()
    if 'if node.id in parent_ids:' in line:
        # Search forward for the error return
        for j in range(i+1, i+20):
            if 'return JsonResponse({\'error\': \'An error occurred\'}, status=400)' in lines[j]:
                indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                lines[j] = indent + "return JsonResponse({'error': 'Cannot set parent to itself or duplicate'}, status=400)\r\n"
                print(f"Fixed logic at line {j+1}")
                break

# Fix 2: would_create_cycle (around line 7016 in view)
# Look for: if would_create_cycle(node.id, parent_ids):
# Then find the block with "An error occurred" and garbage brace.

for i in range(len(lines)):
    line = lines[i].strip()
    if 'if would_create_cycle(node.id, parent_ids):' in line:
        # Search forward for the error return
        start_del = -1
        end_del = -1
        
        for j in range(i+1, i+20):
            if 'return JsonResponse({\'error\': \'An error occurred\'}, status=400)' in lines[j]:
                start_del = j
                # Now search for the garbage brace "}, status=400)"
                for k in range(j+1, j+20):
                    if '}, status=400)' in lines[k]:
                        end_del = k
                        break
                break
        
        if start_del != -1 and end_del != -1:
            # Replace the first line
            indent = lines[start_del][:len(lines[start_del]) - len(lines[start_del].lstrip())]
            lines[start_del] = indent + "return JsonResponse({'error': 'Cycle detected'}, status=400)\r\n"
            
            # Delete lines from start_del+1 to end_del (inclusive)
            # We set them to empty string or remove them. 
            # Removing affects indices, so let's set them to empty comments or blank lines
            # Actually, let's delete them from the list carefully.
            # But we are iterating... so we should collect edits and apply later? 
            # Or just set to blank.
            for k in range(start_del+1, end_del+1):
                lines[k] = "" 
            
            print(f"Fixed logic at line {start_del+1} and cleared garbage up to {end_del+1}")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
