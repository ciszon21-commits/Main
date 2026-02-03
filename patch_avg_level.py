import os

file_path = r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found_team_detail = False
patch_applied = False

for i, line in enumerate(lines):
    if 'def team_detail(' in line:
        found_team_detail = True
    
    if found_team_detail and not patch_applied:
        # Look for the context dictionary initialization after member_stats loop
        if 'context = {' in line and i > 9193: # Start looking after the function def
            # Insert initialization before this line
            new_lines.append('    # 計算平均等級\n')
            new_lines.append('    avg_level = round(sum(m.level for m in members) / len(members), 1) if members else 0\n')
            new_lines.append('\n')
            patch_applied = True
    
    new_lines.append(line)

if patch_applied:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Patch applied successfully.")
else:
    print("Could not find patch point.")
