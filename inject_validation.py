import os
import re

file_path = 'EngineerRPG/views.py'

# Logic to inject:
# Check if node_type is ROOT.
# If so, calculate Total ROOT XP + New Reward (minus old reward if update).
# If > 4500 (XP for Lv 10), return Error.

new_validation = """        # Validate ROOT XP Limit (Lv 10 Cap check)
        # Lv 10 requires ~ 4500 XP (Sum of n*100 for n=1 to 9 is 4500)
        # Actually, let's double check the formula.
        # Lv 1->2: 100
        # ...
        # Lv 9->10: 900
        # Total = 4500.
        MAX_ROOT_XP = 4500
        
        if node.node_type == 'ROOT':
            # Calculate current total ROOT XP (excluding this node if it exists)
            current_root_xp = 0
            root_skills = SkillNode.objects.filter(node_type='ROOT')
            if node.id:
                root_skills = root_skills.exclude(id=node.id)
                
            for s in root_skills:
                current_root_xp += s.exp_reward
                
            new_total = current_root_xp + node.exp_reward
            
            if new_total > MAX_ROOT_XP:
                return JsonResponse({
                    'error': f'共同必修 (ROOT) 總經驗值上限為 {MAX_ROOT_XP} (Lv.10)。目前總計: {new_total}，請調整獎勵值。'
                }, status=400)
"""

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate insertion point: before `node.save()` inside `api_save_skill_node`
# We look for `node.save()` which is around line 6976 in the view_file output.
# But `api_save_skill_node` starts at 6932.

# We need to insert this logic AFTER `node.exp_reward` is set and `node.node_type` is set.
# Looking at Step 377:
# 6958: node_type = ...
# ...
# 6965: node.exp_reward = ...
# ...
# 6976: node.save()

# We can insert before `node.save()`.

pattern = r"(node\.save\(\))"
# We want to insert before the specified pattern, but we need to ensure we are inside the api_save_skill_node function.
# This naive replace might affect other node.save() calls if not careful.
# So let's find the specific block.

# Strategy: Find "node.exp_reward = int(data.get('exp_reward', 50))" and insert after the block dealing with character class logic but before save.
# actually, character class logic is lines 6968-6974.
# Then line 6976 is node.save().

search_str = "node.save()"
insert_marker = "node.exp_reward = int(data.get('exp_reward', 50))"

# Let's find the `api_save_skill_node` function content first.
func_start = content.find("def api_save_skill_node(request):")
if func_start == -1:
    print("Function not found")
    exit(1)

# Find insertion point relative to function start
# We want to insert before node.save() but after all properties are set.
# The closest unique line before save is likely the character class setting block end.
# Or we can insert right before `node.save()` inside this function.

# Let looks for the specific `node.save()` inside this function.
# The function ends when indentation/def changes.
func_end = content.find("def ", func_start + 10)
func_content = content[func_start:func_end] if func_end != -1 else content[func_start:]

# Inside func_content, find the FIRST `node.save()` which corresponds to the initial save.
save_idx = func_content.find("node.save()")

if save_idx != -1:
    # Calculate absolute position
    abs_idx = func_start + save_idx
    
    # Check indentation to match
    # Assuming 8 spaces
    indent = "        " 
    
    # Construct new block
    # We need to verify `node` object has `node_type` and `exp_reward` set.
    # In the code, they are set before save.
    
    updated_content = content[:abs_idx] + new_validation + indent + content[abs_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print("Successfully injected validation logic.")
else:
    print("Could not find insertion point.")

