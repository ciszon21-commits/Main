from EngineerRPG.models import UserProfile

print("Searching for users with recent activity...")

for profile in UserProfile.objects.all():
    print(f"User: {profile.user.username} (Level {profile.level})")
    print(f"  HP: {profile.hp}/{profile.get_total_hp()}")
    total_dr = profile.get_total_damage_reduction()
    print(f"  Total DR: {total_dr}")
    
    print("  Equipped:")
    equipment_slots = [
        profile.equipped_helmet, profile.equipped_armor, profile.equipped_boots,
        profile.equipped_tool_1, profile.equipped_tool_2, profile.equipped_tool_3
    ]
    
    for slot in equipment_slots:
        if slot:
            dr = slot.get_damage_reduction()
            print(f"    - {slot.equipment.name} (+{slot.enhancement_level}): DR={dr}")
            if slot.equipment.enhancement_rules:
                print(f"      Rules: {slot.equipment.enhancement_rules}")

