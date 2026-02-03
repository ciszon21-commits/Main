import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove line 7040 if it contains the generic error return
# Note: Indicies shift. In step 6671 view, it was line 7040.
# We should search for the specific line around there.

target = "                        return JsonResponse({'error': 'An error occurred'}, status=400)"

for i in range(7030, 7060):
    if i < len(lines) and target in lines[i]:
        lines[i] = "" # Delete
        print(f"Deleted line {i+1}")
        break

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
