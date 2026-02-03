import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import Equipment, UserEquipment, UserProfile, CharacterClass

def verify_stats():
    print("Verifying Equipment Stats Logic...")
    
    # Setup dummy user
    user, _ = User.objects.get_or_create(username='test_engineer_stats')
    # Assign class if needed
    c_class, _ = CharacterClass.objects.get_or_create(code='CIVIL', defaults={'name': 'Civil', 'base_hp': 50, 'base_mp': 100})
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'employee_id': 'TEST001', 'character_class': c_class})
    
    # 1. Verify Helmet (T1) Stats Logic
    print("\n[Test 1] Standard Safety Helmet (T1) - MP Growth")
    helmet = Equipment.objects.get(name="標準工地帽")
    u_helmet, _ = UserEquipment.objects.get_or_create(user_profile=profile, equipment=helmet)
    
    levels = [0, 1, 3, 5, 6, 9]
    expected_mp = {0: 10, 1: 10, 3: 15, 5: 15, 6: 20, 9: 30}
    
    for lvl in levels:
        u_helmet.enhancement_level = lvl
        mp = u_helmet.get_total_mp_bonus()
        print(f"  Level +{lvl}: MP Bonus = {mp} (Expected: {expected_mp[lvl]}) -> {'PASS' if mp == expected_mp[lvl] else 'FAIL'}")

    # 2. Verify Chest (T2) Stats Logic (HP + DR)
    print("\n[Test 2] Supervisor Vest (T2) - HP & DR Growth")
    vest = Equipment.objects.get(name="監工戰術背心")
    u_vest, _ = UserEquipment.objects.get_or_create(user_profile=profile, equipment=vest)
    
    # +0: HP 20, DR 2
    # +3: HP 30, DR 2
    # +6: HP 40, DR 2
    # +9: HP 55, DR 3
    test_cases = [
        (0, 20, 2),
        (3, 30, 2),
        (6, 40, 2),
        (9, 55, 3)
    ]
    
    for lvl, exp_hp, exp_dr in test_cases:
        u_vest.enhancement_level = lvl
        hp = u_vest.get_total_hp_bonus()
        dr = u_vest.get_damage_reduction()
        print(f"  Level +{lvl}: HP={hp} (Exp: {exp_hp}), DR={dr} (Exp: {exp_dr}) -> {'PASS' if hp == exp_hp and dr == exp_dr else 'FAIL'}")

    # 3. Verify Tool (App) Stats
    print("\n[Test 3] Inspection App - Shield & Cost")
    app = Equipment.objects.get(name="工程查驗 APP")
    u_app, _ = UserEquipment.objects.get_or_create(user_profile=profile, equipment=app)
    
    # Logic is stored in rules, but get methods (hp/mp) might not cover shield/cost unless we added methods?
    # We didn't add specific methods for shield/cost to UserEquipment, so we verify raw rules access or if we intended to use helper methods.
    # The requirement didn't specify `get_shield()` but logical usage in code.
    # We'll rely on reading `enhancement_rules` directly or via the `_get_stat_from_rules` helper if it was public, but it's protected.
    # However we can access `u_app._get_stat_from_rules('shield', 0)` for testing.
    
    # +0: Shield 20, Cost 20
    # +9: Shield 35, Cost 35
    
    u_app.enhancement_level = 0
    s0 = u_app._get_stat_from_rules('shield', 0)
    c0 = u_app._get_stat_from_rules('cost', 0)
    print(f"  Level +0: Shield={s0} (Exp: 20), Cost={c0} (Exp: 20) -> {'PASS' if s0==20 and c0==20 else 'FAIL'}")

    u_app.enhancement_level = 9
    s9 = u_app._get_stat_from_rules('shield', 0)
    c9 = u_app._get_stat_from_rules('cost', 0)
    print(f"  Level +9: Shield={s9} (Exp: 35), Cost={c9} (Exp: 35) -> {'PASS' if s9==35 and c9==35 else 'FAIL'}")

if __name__ == '__main__':
    verify_stats()
