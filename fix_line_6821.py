import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove line 6821 which contains "}, status=400)"
if 6821 <= len(lines) and '}, status=400)' in lines[6820]:
    del lines[6820]
    print("Deleted line 6821")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
