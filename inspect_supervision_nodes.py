import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import SkillNode

def inspect_nodes():
    node_names = ['監造行政作業基礎', '監造權責與倫理', '專案成本控制與估驗']
    nodes = SkillNode.objects.filter(name__in=node_names)
    
    print(f"{'Name':<20} | {'ID':<5} | {'Type':<10} | {'X':<5} | {'Y':<5} | {'Parents'}")
    print("-" * 70)
    for n in nodes:
        parents = ", ".join([p.name for p in n.parent_skills.all()])
        print(f"{n.name:<20} | {n.id:<5} | {n.node_type:<10} | {n.position_x:<5} | {n.position_y:<5} | {parents}")

if __name__ == "__main__":
    inspect_nodes()
