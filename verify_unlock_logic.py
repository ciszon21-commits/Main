from EngineerRPG.models import Equipment, UserProfile, UserEquipment

# Get a test user (or first user)
profile = UserProfile.objects.first()
print(f"Testing with user: {profile.user.username} (Level {profile.level})")

# Check if all 13 items exist for this user
user_eqs = UserEquipment.objects.filter(user_profile=profile)
print(f"User has {user_eqs.count()} equipment records (expected 13+)")

# Check a high tier item (Tier 3 Helmet) - likely locked if level is low
t3_helmet = Equipment.objects.filter(tier=3, equipment_type='HELMET').first()
if t3_helmet:
    print(f"Checking T3 Helmet: {t3_helmet.name} (Req Level: {t3_helmet.required_level})")
    is_unlocked = profile.level >= t3_helmet.required_level
    print(f"-> Unlocked for user? {is_unlocked}")
    
    # Verify UserEquipment exists
    ue = UserEquipment.objects.filter(user_profile=profile, equipment=t3_helmet).first()
    if ue:
        print(f"-> UserEquipment record exists: ID {ue.id}")
    else:
        print("-> UserEquipment record MISSING!")

# Check a T1 item
t1_helmet = Equipment.objects.filter(tier=1, equipment_type='HELMET').first()
if t1_helmet:
    print(f"Checking T1 Helmet: {t1_helmet.name} (Req Level: {t1_helmet.required_level})")
    is_unlocked = profile.level >= t1_helmet.required_level
    print(f"-> Unlocked for user? {is_unlocked}")
