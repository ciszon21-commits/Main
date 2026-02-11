import re

def get_views_from_urls(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find views.function_name
    views = set(re.findall(r'views\.(\w+)', content))
    return views

def get_defined_views(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find def function_name
    defined = set(re.findall(r'def\s+(\w+)\s*\(', content))
    return defined

if __name__ == "__main__":
    required = get_views_from_urls('EngineerRPG/urls.py')
    defined = get_defined_views('EngineerRPG/views.py')
    
    missing = required - defined
    
    # Filter known external imports if any (but here they are mostly in views.py)
    # views.py imports: edit_team, manage_team_members, create_team from views_team_management
    # So we should check those too
    
    external_views = {'edit_team', 'manage_team_members', 'create_team'}
    really_missing = missing - external_views
    
    with open('missing_views.log', 'w', encoding='utf-8') as f:
        f.write(str(really_missing))
        
    print("Done writing to missing_views.log")
