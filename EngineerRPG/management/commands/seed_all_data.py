"""
從 seed_data.json 重建所有 RPG 系統資料
包含：職業、技能樹(含座標與前置關係)、裝備(含圖片路徑與需求等級)、
      題庫分類、題目、道具、試煉、課程

使用方式：
  python manage.py seed_all_data          # 僅新增不存在的資料
  python manage.py seed_all_data --clear  # 清除後重建所有資料
"""

import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from EngineerRPG.models import (
    CharacterClass, SkillNode, Equipment, QuestionCategory, Question,
    Item, Trial, Course,
)


class Command(BaseCommand):
    help = '從 seed_data.json 重建所有 RPG 系統資料（職業、技能樹、裝備、題庫、課程等）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除所有現有資料後重建（不影響使用者資料）',
        )

    def handle(self, *args, **options):
        clear_mode = options.get('clear', False)
        data = self._load_data()

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('  RPG 系統資料重建'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if clear_mode:
            self.stdout.write(self.style.WARNING(
                '  [!] 清除模式：將刪除裝備/技能/題庫/試煉/課程/道具'))

        with transaction.atomic():
            if clear_mode:
                self._clear_data()

            self._seed_character_classes(data['character_classes'])
            self._seed_question_categories(data['question_categories'])
            self._seed_questions(data['questions'])
            self._seed_skill_nodes(data['skill_nodes'])
            self._seed_equipment(data['equipment'])
            self._seed_items(data['items'])
            self._seed_trials(data['trials'])
            self._seed_courses(data['courses'])

        self._show_statistics()
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('  RPG 系統資料重建完成'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

    # ────────────────────────────────────────────────────
    # Data loading
    # ────────────────────────────────────────────────────

    def _load_data(self):
        data_path = os.path.join(
            os.path.dirname(__file__), 'data', 'seed_data.json')
        if not os.path.exists(data_path):
            raise FileNotFoundError(
                f'找不到 seed_data.json: {data_path}\n'
                '請先執行 export_seed_data 匯出資料。')
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ────────────────────────────────────────────────────
    # Clear
    # ────────────────────────────────────────────────────

    def _clear_data(self):
        # 依賴順序反向刪除，不刪除使用者相關資料
        # CharacterClass 有 PROTECT 保護（被 UserProfile 參照），跳過刪除
        for model, label in [
            (Course, '課程'),
            (Trial, '試煉'),
            (Item, '道具'),
            (Equipment, '裝備'),
            (Question, '題目'),
            (QuestionCategory, '題目分類'),
            (SkillNode, '技能節點'),
        ]:
            count = model.objects.count()
            if count:
                model.objects.all().delete()
                self.stdout.write(f'  - 已清除 {label}: {count} 筆')
        self.stdout.write(f'  - 職業: 保留（被使用者資料參照）')

    # ────────────────────────────────────────────────────
    # 1. CharacterClass
    # ────────────────────────────────────────────────────

    def _seed_character_classes(self, items):
        created = 0
        for d in items:
            _, is_new = CharacterClass.objects.update_or_create(
                code=d['code'],
                defaults={
                    'name': d['name'],
                    'description': d['description'],
                    'base_hp': d['base_hp'],
                    'base_mp': d['base_mp'],
                },
            )
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  [1/8] 職業: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 2. QuestionCategory
    # ────────────────────────────────────────────────────

    def _seed_question_categories(self, items):
        created = 0
        self._cat_id_map = {}
        for d in items:
            obj, is_new = QuestionCategory.objects.update_or_create(
                name=d['name'],
                defaults={'description': d.get('description', '')},
            )
            self._cat_id_map[d['id']] = obj.id
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  [2/8] 題目分類: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 3. Question
    # ────────────────────────────────────────────────────

    def _seed_questions(self, items):
        created = 0
        self._q_id_map = {}
        for d in items:
            cat_id = self._cat_id_map.get(d['category_id']) if d['category_id'] else None
            obj, is_new = Question.objects.update_or_create(
                content=d['content'],
                defaults={
                    'question_type': d['question_type'],
                    'options': d['options'],
                    'correct_answer': d['correct_answer'],
                    'explanation': d.get('explanation', ''),
                    'difficulty': d.get('difficulty', 'B'),
                    'category_id': cat_id,
                    'tags': d.get('tags', ''),
                    'is_active': d.get('is_active', True),
                },
            )
            self._q_id_map[d['id']] = obj.id
            if is_new:
                created += 1
            # M2M: related_skills (set later after skill_nodes created)
        self.stdout.write(self.style.SUCCESS(
            f'  [3/8] 題目: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 4. SkillNode (with coordinates & parent relations)
    # ────────────────────────────────────────────────────

    def _seed_skill_nodes(self, items):
        created = 0
        self._skill_id_map = {}

        # Pass 1: create/update nodes (without parent relations)
        for d in items:
            cc_id = None
            if d['character_class_id']:
                cc = CharacterClass.objects.filter(
                    id=d['character_class_id']).first()
                if cc:
                    cc_id = cc.id
            obj, is_new = SkillNode.objects.update_or_create(
                name=d['name'],
                defaults={
                    'description': d.get('description', ''),
                    'node_type': d['node_type'],
                    'character_class_id': cc_id,
                    'min_level': d.get('min_level', 1),
                    'position_x': d['position_x'],
                    'position_y': d['position_y'],
                    'exp_reward': d.get('exp_reward', 50),
                },
            )
            self._skill_id_map[d['id']] = obj.id
            if is_new:
                created += 1

        # Pass 2: set parent_skills M2M
        for d in items:
            if d.get('parent_ids'):
                obj = SkillNode.objects.get(id=self._skill_id_map[d['id']])
                parent_pks = [
                    self._skill_id_map[pid]
                    for pid in d['parent_ids']
                    if pid in self._skill_id_map
                ]
                obj.parent_skills.set(parent_pks)

        # Pass 3: set question.related_skills (now that skill IDs exist)
        # (read from original data)

        self.stdout.write(self.style.SUCCESS(
            f'  [4/8] 技能節點: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 5. Equipment (with icon path, tier, required_level)
    # ────────────────────────────────────────────────────

    def _seed_equipment(self, items):
        created = 0
        self._eq_id_map = {}
        for d in items:
            req_skill_id = None
            if d.get('required_skill_id') and d['required_skill_id'] in self._skill_id_map:
                req_skill_id = self._skill_id_map[d['required_skill_id']]

            obj, is_new = Equipment.objects.update_or_create(
                name=d['name'],
                defaults={
                    'description': d.get('description', ''),
                    'equipment_type': d['equipment_type'],
                    'rarity': d.get('rarity', 'COMMON'),
                    'tier': d.get('tier', 1),
                    'hp_bonus': d.get('hp_bonus', 0),
                    'mp_bonus': d.get('mp_bonus', 0),
                    'damage_reduction': d.get('damage_reduction', 0),
                    'enhancement_rules': d.get('enhancement_rules', {}),
                    'skill_effect': d.get('skill_effect'),
                    'skill_description': d.get('skill_description'),
                    'mp_cost': d.get('mp_cost', 0),
                    'special_ability_name': d.get('special_ability_name'),
                    'special_ability_description': d.get('special_ability_description'),
                    'required_skill_id': req_skill_id,
                    'required_level': d.get('required_level', 1),
                    'max_enhancement': d.get('max_enhancement', 9),
                    'icon': d.get('icon', ''),
                },
            )
            self._eq_id_map[d['id']] = obj.id
            if is_new:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  [5/8] 裝備: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 6. Item
    # ────────────────────────────────────────────────────

    def _seed_items(self, items):
        created = 0
        self._item_id_map = {}
        # Items may have duplicate names, so match by index within each item_type
        items_by_type = {}
        for d in items:
            items_by_type.setdefault(d['item_type'], []).append(d)

        for item_type, type_items in items_by_type.items():
            existing = list(
                Item.objects.filter(item_type=item_type).order_by('id'))
            for idx, d in enumerate(type_items):
                if idx < len(existing):
                    obj = existing[idx]
                    # Update existing
                    obj.name = d['name']
                    obj.description = d.get('description', '')
                    obj.rarity = d.get('rarity', 'COMMON')
                    obj.effect_type = d.get('effect_type', 'HINT')
                    obj.effect_value = d.get('effect_value', 0)
                    obj.icon = d.get('icon', '')
                    obj.save()
                else:
                    obj = Item.objects.create(
                        name=d['name'],
                        description=d.get('description', ''),
                        item_type=d['item_type'],
                        rarity=d.get('rarity', 'COMMON'),
                        effect_type=d.get('effect_type', 'HINT'),
                        effect_value=d.get('effect_value', 0),
                        icon=d.get('icon', ''),
                    )
                    created += 1
                self._item_id_map[d['id']] = obj.id
        self.stdout.write(self.style.SUCCESS(
            f'  [6/8] 道具: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 7. Trial
    # ────────────────────────────────────────────────────

    def _seed_trials(self, items):
        created = 0
        # Trials need to be matched by ID to allow renaming
        for d in items:
            cat_id = self._cat_id_map.get(d['category_id']) if d['category_id'] else None
            eq_id = self._eq_id_map.get(d['equipment_reward_id']) if d.get('equipment_reward_id') else None
            item_id = self._item_id_map.get(d['item_reward_id']) if d.get('item_reward_id') else None

            # Use update_or_create with 'id' as the lookup field
            obj, is_new = Trial.objects.update_or_create(
                id=d['id'],  # Lookup by ID
                defaults={
                    'title': d['title'],
                    'description': d.get('description', ''),
                    'trial_type': d['trial_type'],
                    'category_id': cat_id,
                    'question_count': d.get('question_count', 10),
                    'time_limit_minutes': d.get('time_limit_minutes', 30),
                    'required_level': d.get('required_level', 1),
                    'exp_reward': d.get('exp_reward', 100),
                    'equipment_reward_id': eq_id,
                    'item_reward_id': item_id,
                    'is_daily': d.get('is_daily', False),
                    'is_active': d.get('is_active', True),
                }
            )
            
            if is_new:
                created += 1

            # M2M: questions
            if d.get('question_ids'):
                q_pks = [
                    self._q_id_map[qid]
                    for qid in d['question_ids']
                    if qid in self._q_id_map
                ]
                obj.questions.set(q_pks)

            # M2M: required_skills
            if d.get('required_skill_ids'):
                s_pks = [
                    self._skill_id_map[sid]
                    for sid in d['required_skill_ids']
                    if sid in self._skill_id_map
                ]
                obj.required_skills.set(s_pks)

        self.stdout.write(self.style.SUCCESS(
            f'  [7/8] 試煉: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # 8. Course
    # ────────────────────────────────────────────────────

    def _seed_courses(self, items):
        created = 0
        for d in items:
            obj, is_new = Course.objects.update_or_create(
                title=d['title'],
                defaults={
                    'description': d.get('description', ''),
                    'content_type': d.get('content_type', 'LINK'),
                    'content_url': d.get('content_url', ''),
                    'content_file': d.get('content_file', ''),
                    'duration_minutes': d.get('duration_minutes', 30),
                    'passing_score': d.get('passing_score', 80),
                    'exam_time_limit': d.get('exam_time_limit', 20),
                },
            )
            if is_new:
                created += 1

            # M2M: skill_nodes
            if d.get('skill_node_ids'):
                s_pks = [
                    self._skill_id_map[sid]
                    for sid in d['skill_node_ids']
                    if sid in self._skill_id_map
                ]
                obj.skill_nodes.set(s_pks)

            # M2M: questions
            if d.get('question_ids'):
                q_pks = [
                    self._q_id_map[qid]
                    for qid in d['question_ids']
                    if qid in self._q_id_map
                ]
                obj.questions.set(q_pks)

        self.stdout.write(self.style.SUCCESS(
            f'  [8/8] 課程: {len(items)} 筆 (新增 {created})'))

    # ────────────────────────────────────────────────────
    # Statistics
    # ────────────────────────────────────────────────────

    def _show_statistics(self):
        self.stdout.write('')
        self.stdout.write('  --- 資料統計 ---')
        self.stdout.write(f'  職業: {CharacterClass.objects.count()} 個')

        skill_count = SkillNode.objects.count()
        root = SkillNode.objects.filter(node_type='ROOT').count()
        core = SkillNode.objects.filter(node_type='CORE').count()
        adv = SkillNode.objects.filter(node_type='ADVANCED').count()
        self.stdout.write(
            f'  技能節點: {skill_count} 個 (共同必修 {root} / 職業核心 {core} / 進階選修 {adv})')

        eq_count = Equipment.objects.count()
        self.stdout.write(f'  裝備: {eq_count} 個'
                          f' (頭盔 {Equipment.objects.filter(equipment_type="HELMET").count()}'
                          f' / 盔甲 {Equipment.objects.filter(equipment_type="ARMOR").count()}'
                          f' / 靴子 {Equipment.objects.filter(equipment_type="BOOTS").count()}'
                          f' / 工具 {Equipment.objects.filter(equipment_type="TOOL").count()})')

        self.stdout.write(f'  題目分類: {QuestionCategory.objects.count()} 個')
        self.stdout.write(f'  題目: {Question.objects.count()} 題')
        self.stdout.write(f'  道具: {Item.objects.count()} 個')
        self.stdout.write(f'  試煉: {Trial.objects.count()} 個')
        self.stdout.write(f'  課程: {Course.objects.count()} 個')
        self.stdout.write('')
