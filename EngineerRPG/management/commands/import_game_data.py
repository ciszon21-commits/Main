"""
從外部 SQLite 資料庫匯入 EngineerRPG 遊戲資料

匯入範圍：
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
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from EngineerRPG.models import (
    CharacterClass, QuestionCategory, SkillNode, Equipment, Item,
    Course, Question, Trial, DailyTrialTask, Achievement
)


class Command(BaseCommand):
    help = '從外部 SQLite 資料庫匯入 EngineerRPG 遊戲資料（不含使用者資料）'

    # 定義需要匯入的模型和對應的表名
    MODELS_CONFIG = {
        'CharacterClass': {
            'model': CharacterClass,
            'table': 'EngineerRPG_characterclass',
            'unique_field': 'code',
            'order': 1,
        },
        'QuestionCategory': {
            'model': QuestionCategory,
            'table': 'EngineerRPG_questioncategory',
            'unique_field': 'name',
            'order': 2,
        },
        'SkillNode': {
            'model': SkillNode,
            'table': 'EngineerRPG_skillnode',
            'unique_field': 'name',
            'order': 3,
            'm2m_fields': {
                'parent_skills': 'EngineerRPG_skillnode_parent_skills',
            },
        },
        'Equipment': {
            'model': Equipment,
            'table': 'EngineerRPG_equipment',
            'unique_field': 'name',
            'order': 4,
        },
        'Item': {
            'model': Item,
            'table': 'EngineerRPG_item',
            'unique_field': 'name',
            'order': 5,
        },
        'QuestionFirst': {
            # Question 需要先匯入才能處理 Course 的 M2M
            'model': Question,
            'table': 'EngineerRPG_question',
            'unique_field': 'content',
            'order': 6,
            'm2m_fields': {
                'related_skills': 'EngineerRPG_question_related_skills',
            },
        },
        'Course': {
            'model': Course,
            'table': 'EngineerRPG_course',
            'unique_field': 'title',
            'order': 7,
            'm2m_fields': {
                'skill_nodes': 'EngineerRPG_course_skill_nodes',
                'questions': 'EngineerRPG_course_questions',
            },
        },
        'Trial': {
            'model': Trial,
            'table': 'EngineerRPG_trial',
            'unique_field': 'title',
            'order': 8,
            'm2m_fields': {
                'questions': 'EngineerRPG_trial_questions',
                'required_skills': 'EngineerRPG_trial_required_skills',
            },
        },
        'DailyTrialTask': {
            'model': DailyTrialTask,
            'table': 'EngineerRPG_dailytrialtask',
            'unique_field': None,  # 使用 date + task_number 組合
            'order': 9,
            'm2m_fields': {
                'questions': 'EngineerRPG_dailytrialtask_questions',
            },
        },
        'Achievement': {
            'model': Achievement,
            'table': 'EngineerRPG_achievement',
            'unique_field': 'name',
            'order': 10,
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            'db_path',
            type=str,
            help='外部 SQLite 資料庫路徑 (例如: eng.sqlite3db)'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='指定要匯入的模型（預設匯入全部）',
            choices=[
                'CharacterClass', 'QuestionCategory', 'SkillNode',
                'Equipment', 'Item', 'Question', 'Course',
                'Trial', 'DailyTrialTask', 'Achievement', 'all'
            ],
            default=['all']
        )
        parser.add_argument(
            '--mode',
            type=str,
            choices=['skip', 'update', 'replace'],
            default='skip',
            help='處理重複資料的模式：skip=跳過已存在, update=更新已存在, replace=刪除後重新匯入'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬執行，不實際寫入資料'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='顯示詳細匯入資訊'
        )

    def handle(self, *args, **options):
        db_path = Path(options['db_path'])

        if not db_path.exists():
            raise CommandError(f'資料庫檔案不存在: {db_path}')

        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        self.mode = options['mode']
        self.selected_models = options['models']

        # ID 映射表（舊 ID -> 新物件）
        self.id_maps = {
            'CharacterClass': {},
            'QuestionCategory': {},
            'SkillNode': {},
            'Equipment': {},
            'Item': {},
            'Question': {},
            'Course': {},
            'Trial': {},
            'DailyTrialTask': {},
            'Achievement': {},
        }

        self.stdout.write(self.style.NOTICE(f'準備從 {db_path} 匯入資料...'))
        if self.dry_run:
            self.stdout.write(self.style.WARNING('【模擬執行模式】不會實際寫入資料'))

        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

            # 檢查資料表是否存在
            self._check_tables()

            # 按順序匯入
            with transaction.atomic():
                if self.dry_run:
                    # 模擬模式下創建 savepoint
                    sid = transaction.savepoint()

                self._import_all()

                if self.dry_run:
                    transaction.savepoint_rollback(sid)
                    self.stdout.write(self.style.WARNING('【模擬執行完成】資料未實際寫入'))

            self.stdout.write(self.style.SUCCESS('✅ 資料匯入完成！'))
            self._print_summary()

        except Exception as e:
            raise CommandError(f'匯入失敗: {e}')
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()

    def _check_tables(self):
        """檢查必要的資料表是否存在"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row['name'] for row in self.cursor.fetchall()}

        required_tables = {config['table'] for config in self.MODELS_CONFIG.values()}
        missing = required_tables - existing_tables

        if missing:
            self.stdout.write(self.style.WARNING(f'警告：缺少資料表: {missing}'))

    def _should_import(self, model_name):
        """檢查是否應該匯入此模型"""
        if 'all' in self.selected_models:
            return True
        # 處理 QuestionFirst -> Question 的映射
        check_name = 'Question' if model_name == 'QuestionFirst' else model_name
        return check_name in self.selected_models

    def _import_all(self):
        """按順序匯入所有模型"""
        # 按 order 排序
        sorted_configs = sorted(
            self.MODELS_CONFIG.items(),
            key=lambda x: x[1]['order']
        )

        for model_name, config in sorted_configs:
            if self._should_import(model_name):
                self._import_model(model_name, config)

    def _import_model(self, model_name, config):
        """匯入單一模型的資料"""
        model = config['model']
        table = config['table']
        display_name = 'Question' if model_name == 'QuestionFirst' else model_name

        self.stdout.write(f'\n📦 匯入 {display_name}...')

        # 檢查表是否存在
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not self.cursor.fetchone():
            self.stdout.write(self.style.WARNING(f'  ⚠️ 資料表 {table} 不存在，跳過'))
            return

        # 讀取資料
        self.cursor.execute(f"SELECT * FROM {table}")
        rows = self.cursor.fetchall()

        if not rows:
            self.stdout.write(f'  ℹ️ 無資料')
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for row in rows:
            row_dict = dict(row)
            old_id = row_dict.pop('id')

            # 處理外鍵關係
            row_dict = self._process_foreign_keys(model_name, row_dict)

            # 處理 JSON 欄位
            row_dict = self._process_json_fields(model, row_dict)

            # 移除不需要的欄位
            row_dict = self._clean_fields(model, row_dict)

            # 處理唯一性檢查和資料寫入
            result = self._save_record(model_name, config, row_dict, old_id)

            if result == 'created':
                created_count += 1
            elif result == 'updated':
                updated_count += 1
            else:
                skipped_count += 1

        # 處理 M2M 關係（需要在所有基本資料匯入後）
        if 'm2m_fields' in config:
            self._process_m2m_relations(model_name, config)

        self.stdout.write(
            f'  ✓ 建立: {created_count}, 更新: {updated_count}, 跳過: {skipped_count}'
        )

    def _process_foreign_keys(self, model_name, row_dict):
        """處理外鍵關係，將舊 ID 映射到新物件"""
        fk_mappings = {
            'SkillNode': {
                'character_class_id': ('CharacterClass', CharacterClass),
            },
            'Equipment': {
                'required_skill_id': ('SkillNode', SkillNode),
            },
            'QuestionFirst': {
                'category_id': ('QuestionCategory', QuestionCategory),
            },
            'Trial': {
                'category_id': ('QuestionCategory', QuestionCategory),
                'equipment_reward_id': ('Equipment', Equipment),
                'item_reward_id': ('Item', Item),
            },
            'DailyTrialTask': {
                'trial_id': ('Trial', Trial),
            },
        }

        if model_name not in fk_mappings:
            return row_dict

        for field, (ref_model_name, ref_model) in fk_mappings[model_name].items():
            if field in row_dict and row_dict[field]:
                old_fk_id = row_dict[field]
                if old_fk_id in self.id_maps[ref_model_name]:
                    row_dict[field] = self.id_maps[ref_model_name][old_fk_id].id
                else:
                    # 嘗試透過其他方式找到對應物件
                    row_dict[field] = None
                    if self.verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'    ⚠️ 找不到外鍵映射: {field}={old_fk_id}'
                            )
                        )

        return row_dict

    def _process_json_fields(self, model, row_dict):
        """處理 JSON 欄位"""
        json_fields = ['options', 'correct_answer', 'condition', 'enhancement_rules', 'answer_details', 'answers']

        for field in json_fields:
            if field in row_dict and row_dict[field]:
                try:
                    if isinstance(row_dict[field], str):
                        row_dict[field] = json.loads(row_dict[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        return row_dict

    def _clean_fields(self, model, row_dict):
        """清理不存在於模型的欄位"""
        model_fields = {f.name for f in model._meta.get_fields()}
        # 加上 _id 後綴的外鍵欄位
        model_fields.update({f'{f.name}_id' for f in model._meta.get_fields() if hasattr(f, 'related_model')})

        # 過濾掉不存在的欄位
        cleaned = {}
        for key, value in row_dict.items():
            if key in model_fields or key.replace('_id', '') in model_fields:
                cleaned[key] = value

        # 移除時間戳記欄位（讓 Django 自動處理）
        for field in ['created_at', 'updated_at', 'obtained_at']:
            cleaned.pop(field, None)

        return cleaned

    def _save_record(self, model_name, config, row_dict, old_id):
        """保存記錄並處理重複情況"""
        model = config['model']
        unique_field = config['unique_field']
        map_key = 'Question' if model_name == 'QuestionFirst' else model_name

        existing = None

        # 查找現有記錄
        if unique_field:
            if unique_field in row_dict:
                try:
                    existing = model.objects.filter(**{unique_field: row_dict[unique_field]}).first()
                except Exception:
                    pass
        elif model_name == 'DailyTrialTask':
            # DailyTrialTask 使用 date + task_number 組合作為唯一鍵
            if 'date' in row_dict and 'task_number' in row_dict:
                existing = model.objects.filter(
                    date=row_dict['date'],
                    task_number=row_dict['task_number']
                ).first()

        if existing:
            if self.mode == 'skip':
                self.id_maps[map_key][old_id] = existing
                return 'skipped'
            elif self.mode == 'update':
                for key, value in row_dict.items():
                    if key != unique_field:
                        setattr(existing, key, value)
                if not self.dry_run:
                    existing.save()
                self.id_maps[map_key][old_id] = existing
                return 'updated'
            elif self.mode == 'replace':
                if not self.dry_run:
                    existing.delete()

        # 創建新記錄
        try:
            obj = model(**row_dict)
            if not self.dry_run:
                obj.save()
            self.id_maps[map_key][old_id] = obj

            if self.verbose:
                display_name = getattr(obj, unique_field, str(old_id)) if unique_field else str(old_id)
                self.stdout.write(f'    + {display_name}')

            return 'created'
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    ✗ 建立失敗: {e}'))
            return 'error'

    def _process_m2m_relations(self, model_name, config):
        """處理 ManyToMany 關係"""
        m2m_fields = config.get('m2m_fields', {})
        map_key = 'Question' if model_name == 'QuestionFirst' else model_name

        for field_name, table_name in m2m_fields.items():
            # 檢查表是否存在
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not self.cursor.fetchone():
                if self.verbose:
                    self.stdout.write(f'    ⚠️ M2M 表 {table_name} 不存在')
                continue

            # 取得表的欄位名稱
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in self.cursor.fetchall()]

            # 確定 from_id 和 to_id 欄位
            from_col = None
            to_col = None
            for col in columns:
                if col == 'id':
                    continue
                if 'from_' in col or col.endswith('_id') and map_key.lower() in col:
                    from_col = col
                elif 'to_' in col or col.endswith('_id'):
                    to_col = col

            if not from_col or not to_col:
                # 嘗試用通用方式
                non_id_cols = [c for c in columns if c != 'id']
                if len(non_id_cols) >= 2:
                    from_col, to_col = non_id_cols[0], non_id_cols[1]

            if not from_col or not to_col:
                if self.verbose:
                    self.stdout.write(f'    ⚠️ 無法確定 M2M 表 {table_name} 的欄位')
                continue

            self.cursor.execute(f"SELECT {from_col}, {to_col} FROM {table_name}")
            relations = self.cursor.fetchall()

            # 確定目標模型
            target_model_name = self._get_m2m_target_model(model_name, field_name)

            for from_id, to_id in relations:
                if from_id in self.id_maps[map_key]:
                    obj = self.id_maps[map_key][from_id]

                    # 查找目標物件
                    target_obj = None
                    if target_model_name and to_id in self.id_maps.get(target_model_name, {}):
                        target_obj = self.id_maps[target_model_name][to_id]

                    if target_obj and not self.dry_run:
                        try:
                            getattr(obj, field_name).add(target_obj)
                        except Exception as e:
                            if self.verbose:
                                self.stdout.write(f'    ⚠️ M2M 關聯失敗: {e}')

    def _get_m2m_target_model(self, model_name, field_name):
        """取得 M2M 關係的目標模型名稱"""
        m2m_targets = {
            'SkillNode': {'parent_skills': 'SkillNode'},
            'QuestionFirst': {'related_skills': 'SkillNode'},
            'Course': {'skill_nodes': 'SkillNode', 'questions': 'Question'},
            'Trial': {'questions': 'Question', 'required_skills': 'SkillNode'},
            'DailyTrialTask': {'questions': 'Question'},
        }
        return m2m_targets.get(model_name, {}).get(field_name)

    def _print_summary(self):
        """印出匯入摘要"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 匯入摘要：')
        self.stdout.write('=' * 50)

        for model_name, id_map in self.id_maps.items():
            count = len(id_map)
            if count > 0:
                self.stdout.write(f'  {model_name}: {count} 筆')
