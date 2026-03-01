import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import SkillNode

def get_node_info(name):
    try:
        n = SkillNode.objects.get(name=name)
        parents = [p.name for p in n.parent_skills.all()]
        return f"{n.name} (ID: {n.id}): Type={n.node_type}, X={n.position_x}, Y={n.position_y}, Parents={parents}\n"
    except SkillNode.DoesNotExist:
        return f"{name} not found\n"

names = ['環景攝影技術', '3D 點雲處理技術', 'VR虛擬實境訓練', '專案成本控制與估驗', '鄰損糾紛處理實務', '無人機操作證照']
with open('tmp_node_data.txt', 'w', encoding='utf-8') as f:
    for name in names:
        f.write(get_node_info(name))
    
    f.write("\nNodes at X=100:\n")
    nodes_at_100 = SkillNode.objects.filter(position_x=100).order_by('position_y')
    for n in nodes_at_100:
        f.write(f"- {n.name} (Y={n.position_y}, ID={n.id})\n")
