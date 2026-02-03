import os

file_path = 'EngineerRPG/views.py'

# New logic for approve_request:
# 1. Update status to APPROVED.
# 2. Determine target rank based on current rank (re-check logic).
# 3. Update profile rank.
# 4. Recalculate level (consume overflow XP).

new_code = """@login_required
def approve_request(request, request_id):
    \"\"\"核准晉升申請\"\"\"
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('engineer_rpg:dashboard')
    
    promotion_request = get_object_or_404(PromotionRequest, id=request_id)
    
    if promotion_request.status == 'PENDING':
        promotion_request.status = 'APPROVED'
        promotion_request.reviewer = request.user
        promotion_request.reviewed_at = timezone.now()
        promotion_request.save()
        
        # 更新申請人職銜與等級
        applicant = promotion_request.applicant
        
        # 決定新職銜
        if applicant.rank == 'INTERN':
             applicant.rank = 'ASSISTANT'
        elif applicant.rank == 'ASSISTANT':
             applicant.rank = 'ENGINEER'
        
        # 重新計算等級 (釋放累積的經驗值)
        # 原本是直接設為 target_level，現在要根據總經驗值重算
        # Import helper here to avoid circular imports at top level if not handled
        from EngineerRPG.utils.level_system import calculate_level_from_xp
        
        new_level, remaining_xp = calculate_level_from_xp(applicant.level, applicant.experience)
        
        # 如果新等級比 target_level 還低 (不應該發生，因為有基本獎勵)，至少升一級
        if new_level <= applicant.level:
            new_level = applicant.level + 1
            
        applicant.level = new_level
        applicant.experience = remaining_xp
        applicant.save()
        
        messages.success(request, f'已核准 {applicant.user.username} 的晉升申請！新職銜：{applicant.get_rank_display()}，等級提升至 Lv.{applicant.level}。')
        
        # 發送通知給申請人 (TODO: Implement notification system)
        
    return redirect('engineer_rpg:promotion_requests')
"""

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'def approve_request(request, request_id):' in line:
        start_line = i
        break

if start_line != -1:
    # Find the end (next function is reject_request)
    for i in range(start_line + 1, len(lines)):
         if 'def reject_request(' in lines[i]:
             # Backtrack to find decorator or blank lines
             end_line = i
             if '@login_required' in lines[i-1] or '@login_required' in lines[i-2]:
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
    print("Successfully updated approve_request in views.py")
else:
    print(f"Could not find function bounds. Start: {start_line}, End: {end_line}")
