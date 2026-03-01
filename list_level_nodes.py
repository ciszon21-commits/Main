import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import SkillNode

def list_level_nodes():
    # Level 0 is X=50
    nodes = SkillNode.objects.filter(position_x=50).order_by('position_y')
    
    print(f"{'Name':<25} | {'ID':<5} | {'Y':<5} | {'Parents'}")
    print("-" * 60)
    for n in nodes:
        parents = ", ".join([p.name for p in n.parent_skills.all()])
        print(f"{n.name:<25} | {n.id:<5} | {n.position_y:<5} | {parents}")

if __name__ == "__main__":
    list_level_nodes()
