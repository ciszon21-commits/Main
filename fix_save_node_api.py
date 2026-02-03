
import os

target_file = r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py'
new_function = """def api_save_skill_node(request):
    \"\"\"Build Skill Tree\"\"\"
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = get_or_create_user_profile(request.user)
        if not profile or profile.role != 'ADMIN':
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        node_id = data.get('id')
        
        if node_id:
            # Update
            node = SkillNode.objects.get(id=node_id)
        else:
            # Create
            node = SkillNode()
            
        node.name = data.get('name')
        
        # Handle node_type: Ensure it's valid
        node_type = data.get('type') or data.get('node_type')
        if not node_type:
             node.node_type = 'ADVANCED' # Default
        else:
             node.node_type = node_type
             
        node.description = data.get('description', '')
        node.exp_reward = int(data.get('exp_reward', 50))
        
        # Character Class
        class_code = data.get('class_code')
        if class_code:
            try:
                char_class = CharacterClass.objects.get(code=class_code)
                node.character_class = char_class
            except CharacterClass.DoesNotExist:
                pass
                
        node.save()
        
        # Handle parent skills
        parent_ids = data.get('parents', [])
        node.parent_skills.clear()
        if parent_ids:
            for pid in parent_ids:
                 try:
                     parent = SkillNode.objects.get(id=pid)
                     node.parent_skills.add(parent)
                 except SkillNode.DoesNotExist:
                     pass
                     
        # Handle courses
        course_ids = data.get('courses', [])
        node.courses.clear()
        if course_ids:
            for cid in course_ids:
                try:
                    course = Course.objects.get(id=cid)
                    node.courses.add(course)
                except Course.DoesNotExist:
                    pass
        
        return JsonResponse({'status': 'success', 'message': 'Saved successfully', 'node': {'id': node.id, 'name': node.name}})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
"""

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip().startswith('def api_save_skill_node(request):'):
        start_idx = i
    
    # Heuristic to find the end of the function (look for the exception handler return or next function)
    if start_idx != -1 and i > start_idx and "return JsonResponse({'error': str(e)}, status=400)" in line:
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
