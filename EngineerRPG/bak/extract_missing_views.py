import subprocess
import re

def get_git_content(revision, file_path):
    cmd = ['git', 'show', f'{revision}:{file_path}']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.stdout

def extract_functions(content, function_names):
    extracted = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r'^def\s+(\w+)\s*\(', line)
        if match:
            func_name = match.group(1)
            if func_name in function_names:
                # Found a function to extract
                func_content = []
                func_content.append(line)
                i += 1
                # Capture function body (indented lines or empty lines)
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() == '' or next_line.startswith(' ') or next_line.startswith('\t') or next_line.startswith('#'):
                        func_content.append(next_line)
                        i += 1
                    elif next_line.startswith('@'): # Decorator for next function
                        break
                    elif next_line.startswith('def '): # Start of next function
                        break
                    elif next_line.startswith('class '): # Start of class
                        break
                    else:
                        # Possibly unindented code, end of function
                        break
                
                extracted.append('\n'.join(func_content))
                continue # loop will check current line again if it broke out
        i += 1
    return extracted

if __name__ == "__main__":
    missing_views = {
        'delete_question', 'delete_course', 'api_auto_distribute_xp', 
        'guild_announcement_delete', 'guild_announcement_create', 
        'create_course', 'course_management', 'guild_announcement_edit', 
        'submit_course_exam', 'guild_announcement_list', 'edit_course', 
        'course_study', 'course_exam', 'delete_user', 'guild_post_detail',
        'question_management', 'create_question', 'edit_question',
        'category_management', 'dungeon_management', 'create_dungeon',
        'edit_dungeon', 'import_questions_view', 'download_template',
        'skill_tree_editor', 'api_user_stats', 'api_skill_tree_data',
        'api_skill_editor_data', 'api_save_skill_layout', 'api_save_skill_node',
        'api_delete_skill_node', 'api_manage_skill_course', 'api_auto_layout_skill_tree',
        'guild_dashboard', 'guild_exchange_list', 'guild_post_create',
        'user_management', 'create_user', 'edit_user', 'delete_user',
        # Add all potential missing ones from the log
    }
    
    # Read missing views from log if accurate, or use set above. 
    # Let's augment the set with the log file content if it exists
    try:
        with open('missing_views.log', 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse the set string e.g. "{'a', 'b'}"
            import ast
            log_missing = ast.literal_eval(content)
            missing_views.update(log_missing)
    except:
        pass
        
    # Remove intentional removals
    intentional = {'user_login', 'user_register', 'user_logout'}
    missing_views = missing_views - intentional
    
    print(f"Extracting {len(missing_views)} functions...")
    
    git_content = get_git_content('b72d150', 'EngineerRPG/views.py')
    extracted_code = extract_functions(git_content, missing_views)
    
    with open('views_missing_append.py', 'w', encoding='utf-8') as f:
        f.write('\n\n# ==================== Restored Missing Views ====================\n\n')
        f.write('\n\n'.join(extracted_code))
        
    print(f"Extracted {len(extracted_code)} functions to views_missing_append.py")
