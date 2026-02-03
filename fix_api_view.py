
import os

target_file = r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py'
new_function = """def api_manage_skill_course(request):
    \"\"\"Manage skill course association\"\"\"
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = get_or_create_user_profile(request.user)
        if not profile or profile.role != 'ADMIN':
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        node_id = data.get('node_id')
        course_id = data.get('course_id')
        action = data.get('action') # 'add' or 'remove'
        
        node = SkillNode.objects.get(id=node_id)
        course = Course.objects.get(id=course_id)
        
        if action == 'add':
            course.skill_nodes.add(node)
        elif action == 'remove':
            course.skill_nodes.remove(node)
            
        return JsonResponse({'status': 'success', 'message': 'Operation successful'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
"""

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip().startswith('def api_manage_skill_course(request):'):
        start_idx = i
    
    if start_idx != -1 and "return JsonResponse({'error': str(e)}, status=400)" in line:
        end_idx = i
        break
    # Fallback endpoint if indentation differs
    if start_idx != -1 and "return JsonResponse" in line and "status=400" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Found function from line {start_idx+1} to {end_idx+1}. Replacing...")
    
    # Keep lines before
    new_lines = lines[:start_idx]
    # Add new function
    new_lines.append(new_function + '\n')
    # Add lines after
    new_lines.extend(lines[end_idx+1:])
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Successfully replaced function.")
else:
    print(f"Could not find function bounds. Start: {start_idx}, End: {end_idx}")
