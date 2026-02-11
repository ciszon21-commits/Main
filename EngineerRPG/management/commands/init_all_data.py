"""
統一初始化所有資料
按正確順序執行所有初始化 commands
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = '統一初始化所有 RPG 系統資料（職業、技能樹、裝備、題庫、課程）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除所有現有資料後重建'
        )

    def handle(self, *args, **options):
        clear_mode = options.get('clear', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🚀 開始初始化所有 RPG 系統資料'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if clear_mode:
            self.stdout.write(self.style.WARNING('\n⚠️  清除模式：將刪除所有現有資料'))
        
        try:
            # 1. 初始化基礎資料（職業）
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('📋 步驟 1/5: 初始化職業資料'))
            self.stdout.write('=' * 80)
            call_command('init_rpg_data')
            
            # 2. 初始化技能樹
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('🌳 步驟 2/5: 初始化技能樹'))
            self.stdout.write('=' * 80)
            call_command('init_skill_tree_v2')
            
            # 3. 初始化裝備
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('⚔️  步驟 3/5: 初始化裝備'))
            self.stdout.write('=' * 80)
            call_command('populate_equipment_v2')
            
            # 4. 初始化題庫
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('📝 步驟 4/5: 初始化題庫'))
            self.stdout.write('=' * 80)
            if clear_mode:
                call_command('init_questions', '--clear')
            else:
                call_command('init_questions')
            
            # 5. 初始化課程
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('📚 步驟 5/5: 初始化課程'))
            self.stdout.write('=' * 80)
            if clear_mode:
                call_command('init_courses', '--clear')
            else:
                call_command('init_courses')
            
            # 完成
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✅ 所有資料初始化完成！'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
            # 顯示統計資訊
            self._show_statistics()
            
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(self.style.SUCCESS('🎉 RPG 系統已準備就緒！'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ 初始化過程中發生錯誤: {str(e)}'))
            raise
    
    def _show_statistics(self):
        """顯示統計資訊"""
        from EngineerRPG.models import (
            CharacterClass, SkillNode, Equipment, 
            Question, QuestionCategory, Course
        )
        
        self.stdout.write('\n📊 資料統計:')
        self.stdout.write(f'   職業: {CharacterClass.objects.count()} 個')
        self.stdout.write(f'   技能節點: {SkillNode.objects.count()} 個')
        self.stdout.write(f'      - 共同必修: {SkillNode.objects.filter(node_type="ROOT").count()} 個')
        self.stdout.write(f'      - 職業核心: {SkillNode.objects.filter(node_type="CORE").count()} 個')
        self.stdout.write(f'      - 進階選修: {SkillNode.objects.filter(node_type="ADVANCED").count()} 個')
        self.stdout.write(f'   裝備: {Equipment.objects.count()} 個')
        self.stdout.write(f'      - 頭盔: {Equipment.objects.filter(equipment_type="HELMET").count()} 個')
        self.stdout.write(f'      - 盔甲: {Equipment.objects.filter(equipment_type="ARMOR").count()} 個')
        self.stdout.write(f'      - 靴子: {Equipment.objects.filter(equipment_type="BOOTS").count()} 個')
        self.stdout.write(f'      - 工具: {Equipment.objects.filter(equipment_type="TOOL").count()} 個')
        self.stdout.write(f'   題目分類: {QuestionCategory.objects.count()} 個')
        self.stdout.write(f'   題目: {Question.objects.count()} 題')
        self.stdout.write(f'   課程: {Course.objects.count()} 個')
