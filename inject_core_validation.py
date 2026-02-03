import os

file_path = 'EngineerRPG/views.py'

# Logic to inject:
# Check if node_type is CORE.
# If so, calculate Total CORE XP (filter by class) + New Reward.
# If > 118000, return Error.

# We locate `MAX_ROOT_XP = 4500` block and add CORE logic after it.

new_validation = """
        MAX_CORE_XP = 118000
        
        if node.node_type == 'CORE':
             current_core_xp = 0
             # Note: node.character_class might not be set yet if it's new and we rely on data.get('class_code')
             # But loop above sets node.character_class.
             
             if not node.character_class:
                 # Try to get from data if not set yet (unlikely given previous logic)
                 pass
                 
             if node.character_class:
                 core_skills = SkillNode.objects.filter(node_type='CORE', character_class=node.character_class)
                 if node.id:
                     core_skills = core_skills.exclude(id=node.id)
                     
                 for s in core_skills:
                     current_core_xp += s.exp_reward
                     
                 new_total = current_core_xp + node.exp_reward
                 
                 if new_total > MAX_CORE_XP:
                     return JsonResponse({
                         'error': f'職業核心 (CORE) 總經驗值上限為 {MAX_CORE_XP} (Lv.50)。目前總計: {new_total}，請調整獎勵值。'
                     }, status=400)
"""

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate insertion point: After the ROOT validation block.
# We look for `MAX_ROOT_XP = 4500` and the end of that if block.

search_str = "MAX_ROOT_XP = 4500"
idx = content.find(search_str)

if idx != -1:
    # Find the end of the ROOT if block. 
    # The ROOT block is:
    # if node.node_type == 'ROOT':
    #    ...
    #    if new_total > MAX_ROOT_XP:
    #         return ... (ends with })
    
    # We can assume strict indentation.
    # We look for the next block or `node.save()`.
    
    # Let's insert before `node.save()`, effectively appending to the validation section.
    # Wait, we already have a validation block injected before `node.save()`.
    # Let's append this new block right after the ROOT block.
    
    # Find `if node.node_type == 'ROOT':`
    root_block_start = content.find("if node.node_type == 'ROOT':", idx)
    # Find next top-level statement (same indentation).
    # Since we injected it, it's indented by 8 spaces.
    
    # Better approach: find `MAX_ROOT_XP = 4500`
    # Then find the closing parenthesis/brace of the response? No.
    # Let's just append to the end of the ROOT block.
    
    # Simple regex to find the end of the ROOT block is hard without parsing.
    # But we know `node.save()` follows these checks.
    # So we can insert BEFORE `node.save()` again, but we must ensure we are after ROOT check.
    
    # Strategy: Replace `node.save()` with `NEW_CORE_LOGIC + node.save()`
    # But wait, we already did that for ROOT.
    # So `node.save()` is preceded by ROOT logic.
    # If we replace `node.save()` again, we add CORE logic after ROOT logic.
    
    # Find the LAST instance of `node.save()` within the function?
    # No, `node.save()` is unique in that function block hopefully.
    
    # Let's just search for `node.save()` again.
    # Since ROOT logic is already there, replacing `node.save()` will put CORE logic AFTER ROOT logic.
    # Perfect.
    
    # Find `api_save_skill_node` again to be safe.
    func_start = content.find("def api_save_skill_node(request):")
    func_end = content.find("def ", func_start + 10)
    func_content = content[func_start:func_end]
    
    # This `node.save()` search must find the one we want.
    # Currently snippet looks like:
    # ...
    # MAX_ROOT_XP = 4500
    # ...
    # node.save()
    
    save_idx = content.find("node.save()", func_start)
    
    if save_idx != -1 and (func_end == -1 or save_idx < func_end):
         indent = "        "
         updated_content = content[:save_idx] + new_validation + indent + content[save_idx:]
         
         with open(file_path, 'w', encoding='utf-8') as f:
             f.write(updated_content)
         print("Successfully injected CORE validation logic.")
    else:
         print("Could not find suitable insertion point.")
else:
    print("Could not find MAX_ROOT_XP marker. Did the previous injection fail?")

