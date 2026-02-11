"""
從 db.sqlite3 匯出裝備、技能樹、題庫等完整資料
"""
import os, sys, json, django

os.environ['DJANGO_SETTINGS_MODULE'] = 'CoDevStudio.settings'
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from EngineerRPG.models import (
    Equipment, SkillNode, CharacterClass,
    Question, QuestionCategory, Course, Trial
)

output = {}

# ── 1. 裝備 ──
print("=" * 60)
print("裝備資料")
print("=" * 60)
equip_list = []
for e in Equipment.objects.all().order_by('equipment_type', 'tier'):
    data = {
        'name': e.name,
        'equipment_type': e.equipment_type,
        'tier': e.tier,
        'description': e.description,
        'icon': e.icon,
        'hp_bonus': e.hp_bonus,
        'mp_bonus': e.mp_bonus,
        'damage_reduction': e.damage_reduction,
        'skill_effect': e.skill_effect,
        'skill_description': e.skill_description,
        'mp_cost': e.mp_cost,
        'special_ability_name': e.special_ability_name,
        'special_ability_description': e.special_ability_description,
        'required_level': e.required_level,
        'required_skill_id': e.required_skill_id,
        'required_skill_name': e.required_skill.name if e.required_skill else None,
        'max_enhancement': e.max_enhancement,
        'enhancement_rules': e.enhancement_rules,
    }
    equip_list.append(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()
output['equipment'] = equip_list

# ── 2. 技能樹 ──
print("\n" + "=" * 60)
print("技能樹資料")
print("=" * 60)
skill_list = []
for s in SkillNode.objects.all().select_related('character_class').prefetch_related('parent_skills').order_by('character_class__code', 'position_y', 'position_x'):
    data = {
        'name': s.name,
        'description': s.description,
        'node_type': s.node_type,
        'character_class_code': s.character_class.code if s.character_class else None,
        'character_class_name': s.character_class.name if s.character_class else None,
        'exp_reward': s.exp_reward,
        'position_x': s.position_x,
        'position_y': s.position_y,
        'parent_skill_names': [p.name for p in s.parent_skills.all()],
    }
    skill_list.append(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print()
output['skills'] = skill_list

# ── 3. 題庫分類 ──
print("\n" + "=" * 60)
print("題庫分類")
print("=" * 60)
cat_list = []
for c in QuestionCategory.objects.all():
    data = {'id': c.id, 'name': c.name, 'code': c.code, 'description': c.description}
    cat_list.append(data)
    print(json.dumps(data, ensure_ascii=False))
output['categories'] = cat_list

# ── 4. 題庫統計 ──
print("\n" + "=" * 60)
print("題庫統計")
print("=" * 60)
q_count = Question.objects.count()
print(f"總題數: {q_count}")
for cat in QuestionCategory.objects.all():
    cnt = Question.objects.filter(category=cat).count()
    print(f"  {cat.name}: {cnt} 題")

# ── 5. 試煉模板 ──
print("\n" + "=" * 60)
print("試煉模板")
print("=" * 60)
for t in Trial.objects.all():
    print(f"  {t.title} | is_daily={t.is_daily} | is_active={t.is_active} | time={t.time_limit_minutes}min | exp={t.exp_reward}")

# ── 6. 課程 ──
print("\n" + "=" * 60)
print("課程資料")
print("=" * 60)
for c in Course.objects.all().prefetch_related('skill_nodes'):
    skill_names = [s.name for s in c.skill_nodes.all()]
    print(f"  {c.title} | type={c.content_type} | {c.duration_minutes}min | skills={skill_names}")

# 寫出 JSON 備份
with open('db_export.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n✅ 已匯出至 db_export.json")
