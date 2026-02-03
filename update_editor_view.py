import os

file_path = 'EngineerRPG/views.py'

# We need to calculate budgets and pass them to context.
# ROOT Limit: 4500
# CORE Limit: 118000

# Logic to inject:
# from django.db.models import Sum
# ...
# root_xp = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
# core_xp = SkillNode.objects.filter(node_type='CORE', character_class__code=selected_class_code).aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0

new_logic = """    # Calculate XP Budgets
    root_xp_current = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    core_xp_current = SkillNode.objects.filter(node_type='CORE', character_class__code=selected_class_code).aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    
    context = {
        'profile': profile,
        'skills': skills,
        'courses': courses,
        'classes': classes,
        'selected_class': selected_class_code,
        # Budget Info
        'root_xp_current': root_xp_current,
        'root_xp_limit': 4500,
        'core_xp_current': core_xp_current,
        'core_xp_limit': 118000,
    }"""

# We'll replace the context definition block.
# Search for context = { ... }

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'context = {' in line:
        start_line = i
        # Find the end of context dict
        for j in range(i + 1, len(lines)):
             if '}' in lines[j] and lines[j].strip() == '}':
                 end_line = j
                 break
        break

if start_line != -1 and end_line != -1:
    # Need to make sure we import Sum if not already imported.
    # We can check or just rely on aggressive update script if imports are missing.
    # But let's check top of file. 
    # Actually, modify context block directly.
    
    print(f"Replacing context block at lines {start_line+1} to {end_line+1}")
    
    # We replace from 'context = {' to '}'
    # But our new logic includes calculations before context.
    
    new_content = lines[:start_line] + [new_logic + '\n'] + lines[end_line+1:]
    
    # Check for imports
    has_sum = False
    for line in lines[:50]:
        if 'from django.db.models import Sum' in line:
            has_sum = True
            break
            
    if not has_sum:
        # Insert import at top
        new_content.insert(0, "from django.db.models import Sum\n")
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    print("Successfully updated skill_tree_editor view.")
else:
    print(f"Could not find context block. Start: {start_line}, End: {end_line}")
