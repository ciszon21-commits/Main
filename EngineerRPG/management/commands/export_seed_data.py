"""
匯出目前資料庫的 RPG 系統資料到 seed_data.json
可搭配 seed_all_data 指令使用

使用方式：
  python manage.py export_seed_data
"""

import json
import os

from django.core.management.base import BaseCommand

from EngineerRPG.models import (
    CharacterClass, SkillNode, Equipment, QuestionCategory, Question,
    Item, Trial, Course,
)


class Command(BaseCommand):
    help = '匯出目前資料庫的 RPG 系統資料到 seed_data.json'

    def handle(self, *args, **options):
        data = {}

        # CharacterClass
        data['character_classes'] = []
        for c in CharacterClass.objects.all().order_by('id'):
            data['character_classes'].append({
                'id': c.id, 'code': c.code, 'name': c.name,
                'description': c.description,
                'base_hp': c.base_hp, 'base_mp': c.base_mp,
            })

        # Equipment
        data['equipment'] = []
        for e in Equipment.objects.all().order_by('id'):
            data['equipment'].append({
                'id': e.id, 'name': e.name, 'description': e.description,
                'equipment_type': e.equipment_type, 'rarity': e.rarity,
                'tier': e.tier,
                'hp_bonus': e.hp_bonus, 'mp_bonus': e.mp_bonus,
                'damage_reduction': e.damage_reduction,
                'enhancement_rules': e.enhancement_rules,
                'skill_effect': e.skill_effect,
                'skill_description': e.skill_description,
                'mp_cost': e.mp_cost,
                'special_ability_name': e.special_ability_name,
                'special_ability_description': e.special_ability_description,
                'required_skill_id': e.required_skill_id,
                'required_level': e.required_level,
                'max_enhancement': e.max_enhancement,
                'icon': str(e.icon),
            })

        # SkillNode
        data['skill_nodes'] = []
        for s in SkillNode.objects.all().order_by('id'):
            parents = list(s.parent_skills.values_list('id', flat=True))
            data['skill_nodes'].append({
                'id': s.id, 'name': s.name, 'description': s.description,
                'node_type': s.node_type,
                'character_class_id': s.character_class_id,
                'min_level': s.min_level,
                'position_x': s.position_x, 'position_y': s.position_y,
                'exp_reward': s.exp_reward,
                'parent_ids': parents,
            })

        # QuestionCategory
        data['question_categories'] = []
        for qc in QuestionCategory.objects.all().order_by('id'):
            data['question_categories'].append({
                'id': qc.id, 'name': qc.name,
                'description': qc.description,
            })

        # Question
        data['questions'] = []
        for q in Question.objects.all().order_by('id'):
            rs = list(q.related_skills.values_list('id', flat=True))
            data['questions'].append({
                'id': q.id, 'content': q.content,
                'question_type': q.question_type,
                'options': q.options,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'difficulty': q.difficulty,
                'category_id': q.category_id,
                'tags': q.tags, 'is_active': q.is_active,
                'related_skill_ids': rs,
                'image': str(q.image),
            })

        # Item
        data['items'] = []
        for i in Item.objects.all().order_by('id'):
            data['items'].append({
                'id': i.id, 'name': i.name,
                'description': i.description,
                'item_type': i.item_type, 'rarity': i.rarity,
                'effect_type': i.effect_type,
                'effect_value': i.effect_value,
                'icon': str(i.icon),
            })

        # Trial
        data['trials'] = []
        for t in Trial.objects.all().order_by('id'):
            q_ids = list(t.questions.values_list('id', flat=True))
            rs_ids = list(t.required_skills.values_list('id', flat=True))
            data['trials'].append({
                'id': t.id, 'title': t.title,
                'description': t.description,
                'trial_type': t.trial_type,
                'category_id': t.category_id,
                'question_count': t.question_count,
                'time_limit_minutes': t.time_limit_minutes,
                'required_level': t.required_level,
                'exp_reward': t.exp_reward,
                'equipment_reward_id': t.equipment_reward_id,
                'item_reward_id': t.item_reward_id,
                'is_daily': t.is_daily, 'is_active': t.is_active,
                'question_ids': q_ids,
                'required_skill_ids': rs_ids,
            })

        # Course
        data['courses'] = []
        for c in Course.objects.all().order_by('id'):
            sn_ids = list(c.skill_nodes.values_list('id', flat=True))
            q_ids = list(c.questions.values_list('id', flat=True))
            data['courses'].append({
                'id': c.id, 'title': c.title,
                'description': c.description,
                'content_type': c.content_type,
                'content_url': c.content_url,
                'content_file': str(c.content_file),
                'skill_node_ids': sn_ids,
                'duration_minutes': c.duration_minutes,
                'question_ids': q_ids,
                'passing_score': c.passing_score,
                'exam_time_limit': c.exam_time_limit,
            })

        # Write
        out_path = os.path.join(
            os.path.dirname(__file__), 'data', 'seed_data.json')
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f'已匯出至: {out_path}'))
        self.stdout.write(f'  職業: {len(data["character_classes"])} 筆')
        self.stdout.write(f'  裝備: {len(data["equipment"])} 筆')
        self.stdout.write(f'  技能節點: {len(data["skill_nodes"])} 筆')
        self.stdout.write(f'  題目分類: {len(data["question_categories"])} 筆')
        self.stdout.write(f'  題目: {len(data["questions"])} 筆')
        self.stdout.write(f'  道具: {len(data["items"])} 筆')
        self.stdout.write(f'  試煉: {len(data["trials"])} 筆')
        self.stdout.write(f'  課程: {len(data["courses"])} 筆')
