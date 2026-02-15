from EngineerRPG.models import UserProfile, Question, DailyTrialProgress

# Fetch the specific user
username = 'SINGLE-AUTH_07729'  # Based on previous debug output
try:
    profile = UserProfile.objects.get(user__username=username)
except UserProfile.DoesNotExist:
    print(f"User {username} not found, picking first available user.")
    profile = UserProfile.objects.first()

print(f"Testing with User: {profile.user.username}")
print(f"Current HP: {profile.hp}/{profile.get_total_hp()}")

# Calculate Total DR
damage_reduction = profile.get_total_damage_reduction()
print(f"Total Damage Reduction (DR): {damage_reduction}")

# Simulate Damage Calculation for different difficulties
difficulties = ['C', 'B', 'A', 'S']
base_damages = {'C': 5, 'B': 10, 'A': 15, 'S': 15}

for diff in difficulties:
    print(f"\n--- Testing Difficulty {diff} ---")
    base_damage = base_damages[diff]
    print(f"Base Damage: {base_damage}")
    
    # 3. [Lighting Optimization]
    if profile.equipped_helmet and profile.equipped_helmet.has_special_ability():
         if profile.equipped_helmet.special_ability_name == '【照明優化】':
             if diff in ['A', 'S']:
                 base_damage = max(1, base_damage - 1)
                 print(f"  [Effect] Lighting Optimization triggered: Base -> {base_damage}")
    
    current_dr = damage_reduction
    
    # 5. [Crisis Protection]
    # Simulate Low HP condition
    # Check if user has the armor
    if profile.equipped_armor and profile.equipped_armor.has_special_ability():
         if profile.equipped_armor.special_ability_name == '【危機防護】':
             total_hp = profile.get_total_hp()
             # Simulate HP < 20%
             print("  [Check] Crisis Protection (HP < 20%) simulation:")
             if True: # Force trigger for testing
                 current_dr *= 2
                 print(f"  [Effect] Crisis Protection triggered: DR {damage_reduction} -> {current_dr}")

    actual_damage = max(1, base_damage - current_dr)
    print(f"Calculated Actual Damage: {actual_damage}")
    
# Check what equipment is actually equipping
print("\n--- Equipment Details ---")
for slot_name in ['equipped_helmet', 'equipped_armor', 'equipped_boots']:
    slot = getattr(profile, slot_name)
    if slot:
        print(f"{slot_name}: {slot.equipment.name} (+{slot.enhancement_level})")
        print(f"  Special Ability: {slot.special_ability_name}")
        print(f"  DR: {slot.get_damage_reduction()}")
    else:
        print(f"{slot_name}: None")
