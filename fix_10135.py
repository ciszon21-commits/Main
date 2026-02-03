import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix 10135 block
# Look for: except UserItem.DoesNotExist:
# Then find success return

for i in range(len(lines)):
    line = lines[i].strip()
    if 'except UserItem.DoesNotExist:' in line:
        # Check next few lines
        success_found = False
        for j in range(i+1, min(i+20, len(lines))):
            if 'return JsonResponse({\'status\': \'success\', \'message\': \'Operation successful\'})' in lines[j]:
                indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                lines[j] = indent + "return JsonResponse({'error': 'Item not found'}, status=404)\r\n"
                success_found = True
                print(f"Fixed logic at line {j+1}")
                
                # Check for redundant except Exception
                # Search forward
                for k in range(j+1, min(j+10, len(lines))):
                    if 'except Exception as e:' in lines[k]:
                        # Delete this line and up to next return?
                        # Or just comment out?
                        # Deleting is cleaner but tricky with multiline returns.
                        # Let's see if there is a matching return error
                        lines[k] = "" # Delete except
                        # Delete next few lines until return
                        for m in range(k+1, min(k+5, len(lines))):
                            lines[m] = "" 
                            if 'return JsonResponse' in lines[m] or 'status=400' in lines[m]:
                                break
                        print(f"Deleted redundant except block starting at {k+1}")
                        break
                break
        if success_found:
            break

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
