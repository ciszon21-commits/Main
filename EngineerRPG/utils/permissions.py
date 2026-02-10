
from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import UserProfile

PRIVILEGE_RANK = {
    'ADVENTURER': 0,
    'OFFICER': 1,
    'MANAGER': 2,
    'ADMIN': 3
}

def get_whitelist_role(user):
    """獲取使用者的白名單角色（最高權限）"""
    if not user.is_authenticated:
        return 'ADVENTURER'
    if user.is_superuser:
        return 'ADMIN'
        
    # 檢查是否有 UserProfile
    try:
        if hasattr(user, 'rpg_profile'):
            profile_role = user.rpg_profile.role
        else:
            profile_role = 'ADVENTURER'
    except:
        profile_role = 'ADVENTURER'
        
    # 檢查白名單
    if hasattr(user, 'admin_whitelist'):
        whitelist_role = user.admin_whitelist.role
    else:
        whitelist_role = 'ADVENTURER'
        
    # 回傳權限比較高的那個
    p_rank = PRIVILEGE_RANK.get(profile_role, 0)
    w_rank = PRIVILEGE_RANK.get(whitelist_role, 0)
    
    return whitelist_role if w_rank > p_rank else profile_role

def has_whitelist_permission(user, required_role):
    """檢查是否有指定權限（包含白名單）"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
        
    user_role = get_whitelist_role(user)
    user_rank = PRIVILEGE_RANK.get(user_role, 0)
    req_rank = PRIVILEGE_RANK.get(required_role, 0)
    
    return user_rank >= req_rank
