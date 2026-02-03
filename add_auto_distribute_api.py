import os

file_path = 'EngineerRPG/views.py'

# Logic for api_auto_distribute_xp
logic = """
@login_required
def api_auto_distribute_xp(request):
    \"\"\"自動分配剩餘經驗值\"\"\"
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
         return JsonResponse({'error': 'Permission denied'}, status=403)
         
    try:
        data = json.loads(request.body)
        dist_type = data.get('type')
        class_code = data.get('class_code')
        
        target_xp = 0
        skills = []
        
        if dist_type == 'ROOT':
            target_xp = 4500
            skills = list(SkillNode.objects.filter(node_type='ROOT'))
        elif dist_type == 'CORE':
            target_xp = 118000
            skills = list(SkillNode.objects.filter(node_type='CORE', character_class__code=class_code))
        else:
            return JsonResponse({'error': 'Invalid type'}, status=400)
            
        if not skills:
            return JsonResponse({'error': 'No skills found'}, status=404)
            
        # Calculate current total
        current_total = sum(s.exp_reward for s in skills)
        gap = target_xp - current_total
        
        if gap <= 0:
            return JsonResponse({'status': 'success', 'message': '已額滿或超標，無需分配'})
            
        # Distribute gap
        count = len(skills)
        base_add = gap // count
        remainder = gap % count
        
        for i, skill in enumerate(skills):
            skill.exp_reward += base_add
            if i < remainder:
                skill.exp_reward += 1
            skill.save()
            
        return JsonResponse({'status': 'success', 'message': f'已將 {gap} XP 分配給 {count} 個技能'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
"""

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Append to end of file
with open(file_path, 'a', encoding='utf-8') as f:
    f.write('\n' + logic + '\n')

print("Successfully added api_auto_distribute_xp view.")
