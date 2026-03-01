from EngineerRPG.models import SkillNode
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

nodes = SkillNode.objects.filter(name__in=['環景攝影技術', '3D 點雲處理技術', 'VR虛擬實境訓練', '專案成本控制與估驗', '鄰損糾紛處理實務'])
for n in nodes:
    print(f'{n.name} (ID: {n.id}): Type={n.node_type}, X={n.position_x}, Y={n.position_y}, Parents={[p.name for p in n.parent_skills.all()]}')
