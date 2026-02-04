"""
匯出 EngineerRPG 遊戲資料到 SQLite 資料庫

匯出範圍：
- CharacterClass (職業)
- QuestionCategory (題目分類)
- SkillNode (技能樹)
- Equipment (裝備)
- Item (道具)
- Course (課程)
- Question (題目)
- Trial (試煉)
- DailyTrialTask (每日任務)
- Achievement (成就)

排除範圍：所有使用者相關資料
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from EngineerRPG.models import (
    CharacterClass, QuestionCategory, SkillNode, Equipment, Item,
    Course, Question, Trial, DailyTrialTask, Achievement
)


class Command(BaseCommand):
    help = '匯出 EngineerRPG 遊戲資料到 SQLite 資料庫（不含使用者資料）'

    # 模型配置
    MODELS_CONFIG = [
        {
            'name': 'CharacterClass',
            'model': CharacterClass,
            'table': 'EngineerRPG_characterclass',
            'fields': ['id', 'code', 'name', 'description', 'base_hp', 'base_mp', 'icon'],
        },
        {
            'name': 'QuestionCategory',
            'model': QuestionCategory,
            'table': 'EngineerRPG_questioncategory',
            'fields': ['id', 'name', 'description', 'icon', 'created_at'],
        },
        {
            'name': 'SkillNode',
            'model': SkillNode,
            'table': 'EngineerRPG_skillnode',
            'fields': [
                'id', 'name', 'description', 'node_type', 'character_class_id',
                'min_level', 'icon_locked', 'icon_unlocked', 'position_x',
                'position_y', 'exp_reward', 'created_at'
            ],
            'm2m_fields': {
                'parent_skills': {
                    'table': 'EngineerRPG_skillnode_parent_skills',
                    'from_col': 'from_skillnode_id',
                    'to_col': 'to_skillnode_id',
                },
            },
        },
        {
            'name': 'Equipment',
            'model': Equipment,
            'table': 'EngineerRPG_equipment',
            'fields': [
                'id', 'name', 'description', 'equipment_type', 'rarity', 'tier',
                'hp_bonus', 'mp_bonus', 'damage_reduction', 'enhancement_rules',
                'skill_effect', 'skill_description', 'mp_cost',
                'special_ability_name', 'special_ability_description',
                'required_skill_id', 'required_level', 'max_enhancement',
                'icon', 'obtain_method', 'obtain_description', 'obtain_trial_id',
                'is_obtainable', 'created_at'
            ],
        },
        {
            'name': 'Item',
            'model': Item,
            'table': 'EngineerRPG_item',
            'fields': [
                'id', 'name', 'description', 'item_type', 'rarity',
                'effect_type', 'effect_value', 'icon',
                'obtain_method', 'obtain_description', 'is_obtainable', 'created_at'
            ],
        },
        {
            'name': 'Question',
            'model': Question,
            'table': 'EngineerRPG_question',
            'fields': [
                'id', 'content', 'question_type', 'options', 'correct_answer',
                'explanation', 'difficulty', 'category_id', 'tags', 'image',
                'is_active', 'created_at', 'updated_at'
            ],
            'm2m_fields': {
                'related_skills': {
                    'table': 'EngineerRPG_question_related_skills',
                    'from_col': 'question_id',
                    'to_col': 'skillnode_id',
                },
            },
        },
        {
            'name': 'Course',
            'model': Course,
            'table': 'EngineerRPG_course',
            'fields': [
                'id', 'title', 'description', 'content_type', 'content_url',
                'content_file', 'duration_minutes', 'passing_score',
                'exam_time_limit', 'created_at'
            ],
            'm2m_fields': {
                'skill_nodes': {
                    'table': 'EngineerRPG_course_skill_nodes',
                    'from_col': 'course_id',
                    'to_col': 'skillnode_id',
                },
                'questions': {
                    'table': 'EngineerRPG_course_questions',
                    'from_col': 'course_id',
                    'to_col': 'question_id',
                },
            },
        },
        {
            'name': 'Trial',
            'model': Trial,
            'table': 'EngineerRPG_trial',
            'fields': [
                'id', 'title', 'description', 'trial_type', 'category_id',
                'question_count', 'time_limit_minutes', 'required_level',
                'exp_reward', 'equipment_reward_id', 'item_reward_id',
                'is_daily', 'refresh_date', 'is_active', 'created_at'
            ],
            'm2m_fields': {
                'questions': {
                    'table': 'EngineerRPG_trial_questions',
                    'from_col': 'trial_id',
                    'to_col': 'question_id',
                },
                'required_skills': {
                    'table': 'EngineerRPG_trial_required_skills',
                    'from_col': 'trial_id',
                    'to_col': 'skillnode_id',
                },
            },
        },
        {
            'name': 'DailyTrialTask',
            'model': DailyTrialTask,
            'table': 'EngineerRPG_dailytrialtask',
            'fields': [
                'id', 'date', 'task_number', 'trial_id', 'is_active', 'created_at'
            ],
            'm2m_fields': {
                'questions': {
                    'table': 'EngineerRPG_dailytrialtask_questions',
                    'from_col': 'dailytrialtask_id',
                    'to_col': 'question_id',
                },
            },
        },
        {
            'name': 'Achievement',
            'model': Achievement,
            'table': 'EngineerRPG_achievement',
            'fields': [
                'id', 'name', 'description', 'achievement_type',
                'condition', 'exp_reward', 'scroll_reward', 'icon'
            ],
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            'output_path',
            type=str,
            nargs='?',
            default=None,
            help='輸出 SQLite 資料庫路徑（預設: game_data_YYYYMMDD.sqlite3db）'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='指定要匯出的模型（預設匯出全部）',
            choices=[
                'CharacterClass', 'QuestionCategory', 'SkillNode',
                'Equipment', 'Item', 'Question', 'Course',
                'Trial', 'DailyTrialTask', 'Achievement', 'all'
            ],
            default=['all']
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='覆蓋現有檔案'
        )

    def handle(self, *args, **options):
        # 設定輸出路徑
        if options['output_path']:
            output_path = Path(options['output_path'])
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Path(f'game_data_{timestamp}.sqlite3db')

        if output_path.exists() and not options['overwrite']:
            raise CommandError(
                f'檔案已存在: {output_path}\n使用 --overwrite 覆蓋現有檔案'
            )

        self.selected_models = options['models']
        self.stdout.write(self.style.NOTICE(f'準備匯出資料到 {output_path}...'))

        try:
            # 如果檔案存在且允許覆蓋，先刪除
            if output_path.exists():
                output_path.unlink()

            self.conn = sqlite3.connect(output_path)
            self.cursor = self.conn.cursor()

            self._export_all()

            self.conn.commit()
            self.stdout.write(self.style.SUCCESS(f'✅ 資料匯出完成！'))
            self.stdout.write(f'   輸出檔案: {output_path.absolute()}')
            self._print_summary()

        except Exception as e:
            raise CommandError(f'匯出失敗: {e}')
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()

    def _should_export(self, model_name):
        """檢查是否應該匯出此模型"""
        if 'all' in self.selected_models:
            return True
        return model_name in self.selected_models

    def _export_all(self):
        """匯出所有模型"""
        self.counts = {}

        for config in self.MODELS_CONFIG:
            if self._should_export(config['name']):
                self._export_model(config)

    def _export_model(self, config):
        """匯出單一模型"""
        model_name = config['name']
        model = config['model']
        table = config['table']
        fields = config['fields']

        self.stdout.write(f'\n📦 匯出 {model_name}...')

        # 建立資料表
        self._create_table(table, fields, model)

        # 匯出資料
        queryset = model.objects.all()
        count = 0

        for obj in queryset:
            values = []
            for field in fields:
                value = self._get_field_value(obj, field)
                values.append(value)

            placeholders = ', '.join(['?' for _ in fields])
            field_names = ', '.join(fields)

            self.cursor.execute(
                f'INSERT INTO {table} ({field_names}) VALUES ({placeholders})',
                values
            )
            count += 1

        self.counts[model_name] = count
        self.stdout.write(f'  ✓ 匯出 {count} 筆資料')

        # 匯出 M2M 關係
        if 'm2m_fields' in config:
            self._export_m2m_relations(config, model)

    def _create_table(self, table, fields, model):
        """建立資料表"""
        field_defs = []

        for field in fields:
            if field == 'id':
                field_defs.append('id INTEGER PRIMARY KEY')
            elif field.endswith('_id'):
                field_defs.append(f'{field} INTEGER')
            elif field in ['created_at', 'updated_at', 'date', 'refresh_date']:
                field_defs.append(f'{field} TEXT')
            elif field in ['is_active', 'is_daily']:
                field_defs.append(f'{field} INTEGER')
            elif field in ['options', 'correct_answer', 'condition', 'enhancement_rules']:
                field_defs.append(f'{field} TEXT')  # JSON as TEXT
            else:
                field_defs.append(f'{field} TEXT')

        create_sql = f'CREATE TABLE IF NOT EXISTS {table} ({", ".join(field_defs)})'
        self.cursor.execute(create_sql)

    def _get_field_value(self, obj, field):
        """取得欄位值"""
        if field.endswith('_id'):
            # 外鍵
            fk_field = field[:-3]  # 移除 _id
            fk_obj = getattr(obj, fk_field, None)
            return fk_obj.id if fk_obj else None
        else:
            value = getattr(obj, field, None)

            # 處理特殊類型
            if value is None:
                return None
            elif isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            elif hasattr(value, 'name'):  # FileField, ImageField
                return value.name if value else None
            elif hasattr(value, 'isoformat'):  # datetime, date
                return value.isoformat()
            elif isinstance(value, bool):
                return 1 if value else 0
            else:
                return value

    def _export_m2m_relations(self, config, model):
        """匯出 ManyToMany 關係"""
        for field_name, m2m_config in config.get('m2m_fields', {}).items():
            table = m2m_config['table']
            from_col = m2m_config['from_col']
            to_col = m2m_config['to_col']

            # 建立 M2M 表
            self.cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {from_col} INTEGER,
                    {to_col} INTEGER
                )
            ''')

            # 匯出關係
            count = 0
            for obj in model.objects.all():
                related_objects = getattr(obj, field_name).all()
                for related in related_objects:
                    self.cursor.execute(
                        f'INSERT INTO {table} ({from_col}, {to_col}) VALUES (?, ?)',
                        (obj.id, related.id)
                    )
                    count += 1

            self.stdout.write(f'    ↳ {field_name}: {count} 筆關聯')

    def _print_summary(self):
        """印出匯出摘要"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 匯出摘要：')
        self.stdout.write('=' * 50)

        total = 0
        for model_name, count in self.counts.items():
            self.stdout.write(f'  {model_name}: {count} 筆')
            total += count

        self.stdout.write('-' * 50)
        self.stdout.write(f'  總計: {total} 筆')
