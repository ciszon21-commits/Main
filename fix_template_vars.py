
import os

file_path = r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\templates\EngineerRPG\equipment_inventory.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = 312 - 1  # 0-indexed
end_line = 760 - 1    # 0-indexed

modified_lines = []
for i, line in enumerate(lines):
    if start_line <= i <= end_line:
        # Check if line contains user_equipment or is_unlocked
        # We need to be careful not to double-replace if I run this twice, but for now it's clean.
        # Strict replacement:
        # Avoid partial matches? "user_equipment" is distinct enough.
        
        # Replace user_equipment -> item.user_equipment
        # But we must NOT replace "item.user_equipment" if it was already there (unlikely).
        # And we must NOT replace "user_equipment" if it's part of "user_equipment_list" (not used here).
        
        new_line = line
        
        # Replace is_unlocked first to avoid overlap issues (though none obvious)
        new_line = new_line.replace('is_unlocked', 'item.is_unlocked')
        
        # Replace user_equipment
        new_line = new_line.replace('user_equipment', 'item.user_equipment')
        
        # Correction: If the generic replacement created "item.item.user_equipment" (if "item.user_equipment" existed), fix it.
        # But the source has "item.user_equipment" in the {% with %} line which IS DELETED.
        # Wait, the "for item in helmets" line uses "item".
        # It does NOT use "user_equipment".
        
        modified_lines.append(new_line)
    else:
        modified_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(modified_lines)

print("Successfully updated template variables.")
