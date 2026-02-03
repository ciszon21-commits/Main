import os

file_path = 'EngineerRPG/views.py'

new_code = """@login_required
def apply_promotion(request):
    \"\"\"申請晉升\"\"\"
    profile = get_or_create_user_profile(request.user)
    
    # Check for pending request
    pending_request = PromotionRequest.objects.filter(
        applicant=profile,
        status='PENDING'
    ).first()
    
    if pending_request:
        messages.warning(request, '您已有審核中的晉升申請，請耐心等候。')
        return redirect('engineer_rpg:dashboard')
    
    # 決定目標職銜與檢查條件
    current_rank = profile.rank
    target_rank = None
    
    if current_rank == 'INTERN':
        # 實習生 -> 助理工程師
        # 條件：共同必修 (ROOT) 技能 100% 完成
        required_root = SkillNode.objects.filter(node_type='ROOT')
        completed_root = UserSkill.objects.filter(
            user_profile=profile,
            skill_node__in=required_root,
            status='COMPLETED'
        ).count()
        
        if completed_root < required_root.count():
            messages.error(request, '申請失敗：需完成所有「共同必修」技能才可申請成為助理工程師。')
            return redirect('engineer_rpg:skill_tree')
            
        target_rank = 'ASSISTANT'
        
    elif current_rank == 'ASSISTANT':
        # 助理工程師 -> 工程師
        # 條件：職業核心 (CORE) 技能完成度 > 50%
        required_core = SkillNode.objects.filter(
            character_class=profile.character_class,
            node_type='CORE'
        )
        completed_core = UserSkill.objects.filter(
            user_profile=profile,
            skill_node__in=required_core,
            status='COMPLETED'
        ).count()
        
        total_core = required_core.count()
        if total_core > 0 and (completed_core / total_core) < 0.5:
            messages.error(request, '申請失敗：需完成 50% 以上「職業核心」技能才可申請成為工程師。')
            return redirect('engineer_rpg:skill_tree')
            
        target_rank = 'ENGINEER'

    elif current_rank == 'ENGINEER':
        messages.info(request, '您已是正式工程師，無需再申請基礎晉升。')
        return redirect('engineer_rpg:dashboard')
        
    else:
        messages.error(request, '未知的職銜狀態。')
        return redirect('engineer_rpg:dashboard')

    # 建立晉升申請
    target_level = profile.level + 1
    
    promotion_request = PromotionRequest.objects.create(
        applicant=profile,
        current_level=profile.level,
        target_level=target_level,
        status='PENDING'
    )
    
    # 我們可以將 target_rank 存入備註或日誌，或者依據 level 推算 (暫不更動模型)
    # 但為了讓審核者知道，我們可以 update 申請單的備註? 
    # PromotionRequest 有 review_comment，但那是審核者寫的。
    # 暫時依賴 approve_request 裡的邏輯重判。
    
    messages.success(request, f'已成功送出晉升申請！')
    return redirect('engineer_rpg:dashboard')
"""

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'def apply_promotion(request):' in line:
        start_line = i
        break

if start_line != -1:
    # Find the start of the next function to define the end of this one
    for i in range(start_line + 1, len(lines)):
        if line.startswith('def ') or line.startswith('@login_required'):
            # This logic is too simple, might catch decorators.
            pass
        
        if 'def promotion_trial(request, request_id):' in lines[i]:
            # The next function starts here, so the previous one ended at i - (blanks)
            # We will search for the @login_required above it
             end_line = i 
             # Backtrack to find the decorator
             if '@login_required' in lines[i-1] or '@login_required' in lines[i-2] or '@login_required' in lines[i-3] or '@login_required' in lines[i-4]:
                 # Check lines going back
                 for j in range(1, 10):
                     if '@login_required' in lines[i-j]:
                         end_line = i - j
                         break
             break

if start_line != -1 and end_line != -1:
    print(f"Replacing lines {start_line+1} to {end_line}")
    new_content = lines[:start_line] + [new_code + '\n\n'] + lines[end_line:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    print("Successfully updated views.py")
else:
    print(f"Could not find function bounds. Start: {start_line}, End: {end_line}")
