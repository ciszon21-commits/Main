
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile

def check_user_equipment():
    users = User.objects.all()
    print(f"Total Users: {users.count()}")
    for user in users:
        try:
            profile = UserProfile.objects.get(user=user)
            print(f"\nUser: {user.username} (ID: {user.id})")
            
            tools = []
            if profile.equipped_tool_1:
                tools.append(f"Slot 1: {profile.equipped_tool_1.equipment.name} (ID: {profile.equipped_tool_1.equipment.id})")
            if profile.equipped_tool_2:
                tools.append(f"Slot 2: {profile.equipped_tool_2.equipment.name} (ID: {profile.equipped_tool_2.equipment.id})")
            if profile.equipped_tool_3:
                tools.append(f"Slot 3: {profile.equipped_tool_3.equipment.name} (ID: {profile.equipped_tool_3.equipment.id})")
            
            if tools:
                print("Equipped Tools:")
                for t in tools:
                    print(f"  - {t}")
            else:
                print("No tools equipped.")
                
            # Check logic
            has_app = (
                (profile.equipped_tool_1 and profile.equipped_tool_1.equipment.id == 10) or
                (profile.equipped_tool_2 and profile.equipped_tool_2.equipment.id == 10) or
                (profile.equipped_tool_3 and profile.equipped_tool_3.equipment.id == 10)
            )
            print(f"Has Engineering App (Logic Check): {has_app}")
            
        except UserProfile.DoesNotExist:
            print(f"User: {user.username} - No Profile")

if __name__ == "__main__":
    check_user_equipment()
