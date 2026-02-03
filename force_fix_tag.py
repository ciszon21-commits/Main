
import re

file_path = r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\templates\EngineerRPG\equipment_inventory.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern: {% if ... max_enhancement [newline] %}
# We want to match explicitly the split tag we saw.
pattern = r'({% if item\.user_equipment\.enhancement_level < item\.user_equipment\.equipment\.max_enhancement)\s*\n\s*(%})'

def replacement(match):
    print(f"Found match: {match.group(0)!r}")
    return f"{match.group(1)} {match.group(2)}"

new_content, count = re.subn(pattern, replacement, content)

if count > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Fixed {count} split tags.")
else:
    print("No split tags found matching the pattern.")
