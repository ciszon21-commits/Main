
def has_whitelist_permission_code():
    return '''
def has_whitelist_permission(user, required_role='MANAGER'):
    """檢查使用者是否有特定層級的白名單權限"""
    if user.is_superuser:
        return True
    
    # 權限層級定義
    ROLE_LEVELS = {
        'ADVENTURER': 0,
        'OFFICER': 1,
        'MANAGER': 2,
        'ADMIN': 3
    }
    
    try:
        profile = get_or_create_user_profile(user)
        user_role = profile.role
    except:
        return False
        
    user_level = ROLE_LEVELS.get(user_role, 0)
    req_level = ROLE_LEVELS.get(required_role, 0)
    
    return user_level >= req_level
'''

with open('views_missing_append.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Replace RPGTeam -> Team
content = content.replace('RPGTeam', 'Team')
content = content.replace('RPGTeamMember', 'TeamMembership')

# Add helper function
final_content = has_whitelist_permission_code() + "\n" + content

with open('EngineerRPG/views.py', 'a', encoding='utf-8') as f:
    f.write("\n" + final_content)
    
print("Appended restored views to EngineerRPG/views.py")
