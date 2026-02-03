import os

file_path = 'EngineerRPG/views.py'

# We need to find the while loop that handles leveling and inject the cap check.
# The while loop is: 
# while profile.experience >= profile.experience_to_next_level() and profile.level < 100:

new_logic = """        # 瑼Ｘ?臬??
        # Level Cap Logic:
        # Intern -> Cap at 10
        # Assistant -> Cap at 50
        # Engineer -> Cap at 100
        
        while profile.experience >= profile.experience_to_next_level():
            # Check Level Caps
            if profile.rank == 'INTERN' and profile.level >= 10:
                break
            if profile.rank == 'ASSISTANT' and profile.level >= 50:
                break
            if profile.level >= 100:
                break
                
            profile.experience -= profile.experience_to_next_level()
            profile.level += 1
            messages.success(request, f'恭喜升級！等級提升至 {profile.level}！')
            
            # HP/MP growth logic (if any)
            if profile.level % 10 == 0:
                # e.g. bonus
                pass

        # Notification Logic
        if profile.rank == 'ASSISTANT':
             # Check if eligible for Engineer promotion ( > 50% CORE skills)
             req_core = SkillNode.objects.filter(character_class=profile.character_class, node_type='CORE').count()
             done_core = UserSkill.objects.filter(
                 user_profile=profile, 
                 skill_node__character_class=profile.character_class,
                 skill_node__node_type='CORE',
                 status='COMPLETED'
             ).count()
             
             if req_core > 0 and (done_core / req_core) >= 0.5:
                 # Check if recently qualified (e.g. just passed the threshold)
                 # Simpler: just notify every time they complete a skill if they are eligible
                 messages.info(request, '【系統通知】您已完成超過 50% 的職業核心技能，具備晉升「工程師」的資格！請至儀表板申請晉升。')
"""

# The file content in the view_file (Step 352) shows specific lines around 1511.
# I will read the file, locate the while loop, and replace it.

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'while profile.experience >= profile.experience_to_next_level()' in line:
        start_line = i
        # Now find the end of the while loop block.
        # It ends when indentation returns to matching the while loop or less.
        # The while loop indentation seems to be 8 spaces (inside if, inside try/def).
        
        # Look for indentation.
        current_indent = len(line) - len(line.lstrip())
        
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == '': continue
            next_indent = len(lines[j]) - len(lines[j].lstrip())
            if next_indent <= current_indent:
                end_line = j
                break
        else:
             end_line = len(lines)
        break

if start_line != -1 and end_line != -1:
    print(f"Replacing while loop at lines {start_line+1} to {end_line}")
    new_content = lines[:start_line] + [new_logic + '\n'] + lines[end_line:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    print("Successfully updated XP gain logic in views.py")
else:
    print(f"Could not find while loop. Start: {start_line}, End: {end_line}")
