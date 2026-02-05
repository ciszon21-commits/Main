"""
初始化 EngineerRPG 系統資料
建立三大職業與基礎裝備
"""

from django.core.management.base import BaseCommand
from EngineerRPG.models import CharacterClass, Equipment


class Command(BaseCommand):
    help = '初始化 EngineerRPG 系統資料'

    def handle(self, *args, **options):
        self.stdout.write('開始初始化資料...')
        
        # 建立三大職業
        self.create_character_classes()
        
        # 建立基礎裝備
        self.create_basic_equipment()
        
        self.stdout.write(self.style.SUCCESS('✅ 資料初始化完成！'))

    def create_character_classes(self):
        """建立三大職業"""
        classes = [
            {
                'code': 'CIVIL',
                'name': '土木戰士 (Civil Warrior)',
                'description': '專精結構、大地、混凝土等土木工程領域，以堅實的基礎知識守護工程品質。擅長結構分析、地質調查、混凝土品質控制等技能。',
                'base_hp': 5,
                'base_mp': 80,
            },
            {
                'code': 'ME',
                'name': '機電法師 (M&E Mage)',
                'description': '專精水電、空調、消防等機電系統，運用技術魔法確保設施運作順暢。擅長電氣系統、給排水設計、空調控制等技能。',
                'base_hp': 3,
                'base_mp': 120,
            },
            {
                'code': 'SAFETY',
                'name': '職安僧侶 (Safety Monk)',
                'description': '專精職安法規、風險評估、緊急應變，守護工地安全與人員健康。擅長危害辨識、安全檢查、事故預防等技能。',
                'base_hp': 4,
                'base_mp': 100,
            },
        ]
        
        for class_data in classes:
            char_class, created = CharacterClass.objects.get_or_create(
                code=class_data['code'],
                defaults=class_data
            )
            if created:
                self.stdout.write(f'  ✓ 建立職業：{char_class.name}')
            else:
                self.stdout.write(f'  - 職業已存在：{char_class.name}')

    def create_basic_equipment(self):
        """建立基礎裝備"""
        equipment_list = [
            # 防具類
            {
                'name': '基礎安全帽',
                'description': '符合 CNS 標準的基本安全帽，提供頭部基礎防護。',
                'equipment_type': 'HELMET',
                'rarity': 'COMMON',
                'hp_bonus': 1,
                'mp_bonus': 0,
                'required_level': 1,
                'max_enhancement': 3,
            },
            {
                'name': '高級安全帽',
                'description': '具備通風設計與加強防護的高級安全帽。',
                'equipment_type': 'HELMET',
                'rarity': 'RARE',
                'hp_bonus': 2,
                'mp_bonus': 0,
                'required_level': 5,
                'max_enhancement': 5,
            },
            {
                'name': '反光背心',
                'description': '高能見度反光背心，確保工地安全。',
                'equipment_type': 'ARMOR',
                'rarity': 'COMMON',
                'hp_bonus': 1,
                'mp_bonus': 0,
                'required_level': 1,
                'max_enhancement': 3,
            },
            {
                'name': '防護雨鞋',
                'description': '防滑、防水的專業工地雨鞋。',
                'equipment_type': 'BOOTS',
                'rarity': 'COMMON',
                'hp_bonus': 1,
                'mp_bonus': 0,
                'required_level': 1,
                'max_enhancement': 3,
            },
            
            # 工具類
            {
                'name': 'DJI 無人機',
                'description': '專業級無人機，可進行高空拍攝與檢測。',
                'equipment_type': 'TOOL_UAV',
                'rarity': 'EPIC',
                'hp_bonus': 0,
                'mp_bonus': 20,
                'skill_effect': '上帝視角',
                'skill_description': '在試煉中可刪除一個錯誤選項',
                'mp_cost': 30,
                'required_level': 10,
                'max_enhancement': 5,
            },
            {
                'name': '360° 環景相機',
                'description': '可拍攝全景照片的專業相機，用於工地紀錄。',
                'equipment_type': 'TOOL_CAMERA',
                'rarity': 'RARE',
                'hp_bonus': 0,
                'mp_bonus': 15,
                'skill_effect': '全景視野',
                'skill_description': '顯示題目相關的圖片提示',
                'mp_cost': 20,
                'required_level': 8,
                'max_enhancement': 5,
            },
            {
                'name': 'AR 智慧眼鏡',
                'description': '擴增實境智慧眼鏡，可即時顯示 BIM 模型。',
                'equipment_type': 'TOOL_GLASSES',
                'rarity': 'LEGENDARY',
                'hp_bonus': 0,
                'mp_bonus': 30,
                'skill_effect': '透視眼',
                'skill_description': '顯示 3D 模型提示與結構分析',
                'mp_cost': 40,
                'required_level': 15,
                'max_enhancement': 10,
            },
            {
                'name': '工程查驗 APP',
                'description': '整合法規與檢查表的智慧查驗應用程式。',
                'equipment_type': 'TOOL_APP',
                'rarity': 'RARE',
                'hp_bonus': 0,
                'mp_bonus': 10,
                'skill_effect': '快速檢索',
                'skill_description': '標示題目中的關鍵法規條文',
                'mp_cost': 15,
                'required_level': 5,
                'max_enhancement': 5,
            },
        ]
        
        for eq_data in equipment_list:
            equipment, created = Equipment.objects.get_or_create(
                name=eq_data['name'],
                defaults=eq_data
            )
            if created:
                self.stdout.write(f'  ✓ 建立裝備：{equipment.name} ({equipment.get_rarity_display()})')
            else:
                self.stdout.write(f'  - 裝備已存在：{equipment.name}')
