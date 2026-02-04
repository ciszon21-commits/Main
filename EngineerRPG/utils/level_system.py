from EngineerRPG.models import SkillNode, UserSkill

def calculate_level_from_xp(current_level, current_xp):
    """
    Simulate level calculation based on current XP.
    Since the formula is next_level_xp = level * 100, 
    we need to iteratively calculate how many levels can be gained.
    Returns: (new_level, remaining_xp)
    """
    level = current_level
    xp = current_xp
    
    while True:
        xp_needed = level * 100
        if xp >= xp_needed:
            xp -= xp_needed
            level += 1
        else:
            break
            
    return level, xp

def can_gain_xp(profile, amount):
    """
    Check if the user is capped.
    Intern (INTERN): Capped at Lv 10.
    Assistant (ASSISTANT): Capped at Lv 50.
    Engineer (ENGINEER): No cap (max Lv 100).
    """
    if profile.rank == 'INTERN' and profile.level >= 10:
        return False
    if profile.rank == 'ASSISTANT' and profile.level >= 50:
        return False
    if profile.level >= 100:
        return False
        
    return True
