import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'CoDevStudio.settings'

import django
django.setup()

from EngineerRPG.models import CharacterClass
from EngineerRPG.utils.skill_layout import calculate_layout_data

for cc in CharacterClass.objects.all():
    print(f"\n=== {cc.name} ({cc.code}) ===")
    data = calculate_layout_data(cc.code)
    for d in data:
        if d['parent_ids']:
            print(f"  id={d['id']}, name={d['name']}, type={d['node_type']}, parents={d['parent_ids']}")

# Also show raw parent data (before reduction) for comparison
print("\n=== RAW PARENT DATA (no reduction) ===")
from EngineerRPG.models import SkillNode
from django.db.models import Q
for cc in CharacterClass.objects.all():
    print(f"\n--- {cc.name} ({cc.code}) ---")
    skills = SkillNode.objects.filter(
        Q(node_type='ROOT') | Q(character_class__code=cc.code)
    ).prefetch_related('parent_skills')
    for s in skills:
        raw_parents = [p.id for p in s.parent_skills.all()]
        if raw_parents:
            print(f"  id={s.id}, name={s.name}, raw_parents={raw_parents}")
