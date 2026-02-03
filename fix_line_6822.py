import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove line 6822 which contains "}, status=400)"
if 6822 <= len(lines):
    # Check if line 6822 (index 6821) contains the problematic text
    if '}, status=400)' in lines[6821]:
        del lines[6821]
        print("Deleted line 6822")
    else:
        print(f"Line 6822 contains: {lines[6821][:50]}")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
