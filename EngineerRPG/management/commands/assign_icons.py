"""
自動分配裝備和道具圖示
根據裝備類型和現有圖示檔案進行配對
"""

from django.core.management.base import BaseCommand
from EngineerRPG.models import Equipment, Item
import os
from pathlib import Path


class Command(BaseCommand):
    help = '自動分配裝備和道具圖示'

    # 圖示檔案對應表
    EQUIPMENT_ICONS = {
        'HELMET': [
            'EngineerRPG/img/equipment_icons/icon_1_HELMET.png',
            'EngineerRPG/img/equipment_icons/icon_2_HELMET.png',
            'EngineerRPG/img/equipment_icons/icon_3_HELMET.png',
            'EngineerRPG/img/equipment_icons/icon_4_HELMET.png',
            'EngineerRPG/img/equipment_icons/icon_5_HELMET.png',
            'EngineerRPG/img/equipment_icons/helmet.png',
        ],
        'ARMOR': [
            'EngineerRPG/img/equipment_icons/icon_3_ARMOR.png',
            'EngineerRPG/img/equipment_icons/icon_2_ARMOR.png',
            'EngineerRPG/img/equipment_icons/icon_6_ARMOR.png',
            'EngineerRPG/img/equipment_icons/icon_7_ARMOR.png',
            'EngineerRPG/img/equipment_icons/icon_8_ARMOR.png',
            'EngineerRPG/img/equipment_icons/vest.png',
        ],
        'BOOTS': [
            'EngineerRPG/img/equipment_icons/icon_4_BOOTS.png',
            'EngineerRPG/img/equipment_icons/icon_9_BOOTS.png',
            'EngineerRPG/img/equipment_icons/icon_10_BOOTS.png',
            'EngineerRPG/img/equipment_icons/icon_11_BOOTS.png',
            'EngineerRPG/img/equipment_icons/boots.png',
        ],
        'TOOL': [
            'EngineerRPG/img/equipment_icons/icon_5_TOOL_UAV.png',
            'EngineerRPG/img/equipment_icons/icon_6_TOOL_CAMERA.png',
            'EngineerRPG/img/equipment_icons/icon_7_TOOL_GLASSES.png',
            'EngineerRPG/img/equipment_icons/icon_8_TOOL_APP.png',
            'EngineerRPG/img/equipment_icons/icon_12_TOOL.png',
            'EngineerRPG/img/equipment_icons/icon_13_TOOL.png',
            'EngineerRPG/img/equipment_icons/icon_14_TOOL.png',
            'EngineerRPG/img/equipment_icons/icon_15_TOOL.png',
            'EngineerRPG/img/equipment_icons/uav.png',
            'EngineerRPG/img/equipment_icons/camera360.png',
            'EngineerRPG/img/equipment_icons/smart_glasses.png',
            'EngineerRPG/img/equipment_icons/inspection_app.png',
        ],
    }

    # 特定裝備名稱對應
    EQUIPMENT_NAME_MAPPING = {
        '基礎安全帽': 'EngineerRPG/img/equipment_icons/icon_1_HELMET.png',
        '高級安全帽': 'EngineerRPG/img/equipment_icons/icon_2_HELMET.png',
        '標準工地帽': 'EngineerRPG/img/equipment_icons/icon_3_HELMET.png',
        '反光背心': 'EngineerRPG/img/equipment_icons/icon_3_ARMOR.png',
        '勞工戰術背心': 'EngineerRPG/img/equipment_icons/icon_6_ARMOR.png',
        '外骨骼動力外套': 'EngineerRPG/img/equipment_icons/icon_7_ARMOR.png',
        '防護雨鞋': 'EngineerRPG/img/equipment_icons/icon_4_BOOTS.png',
        '絕緣安全鞋': 'EngineerRPG/img/equipment_icons/icon_9_BOOTS.png',
        '動力裝甲靴': 'EngineerRPG/img/equipment_icons/icon_10_BOOTS.png',
        'DJI 無人機': 'EngineerRPG/img/equipment_icons/icon_5_TOOL_UAV.png',
        'UAV 監造無人機': 'EngineerRPG/img/equipment_icons/icon_5_TOOL_UAV.png',
        '360° 環景相機': 'EngineerRPG/img/equipment_icons/icon_6_TOOL_CAMERA.png',
        '360 環景相機': 'EngineerRPG/img/equipment_icons/icon_6_TOOL_CAMERA.png',
        'AR 智慧眼鏡': 'EngineerRPG/img/equipment_icons/icon_7_TOOL_GLASSES.png',
        'AR 智慧工安帽': 'EngineerRPG/img/equipment_icons/icon_7_TOOL_GLASSES.png',
        'VR 安全訓練模擬器': 'EngineerRPG/img/equipment_icons/icon_7_TOOL_GLASSES.png',
        '工程查驗 APP': 'EngineerRPG/img/equipment_icons/icon_8_TOOL_APP.png',
        '理賠型探測儀': 'EngineerRPG/img/equipment_icons/icon_12_TOOL.png',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬執行，不實際更新資料庫'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制覆蓋已有圖示的項目'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('【模擬執行模式】'))

        self.stdout.write('\n=== 分配裝備圖示 ===')
        self._assign_equipment_icons(dry_run, force)

        self.stdout.write('\n=== 分配道具圖示 ===')
        self._assign_item_icons(dry_run, force)

        self.stdout.write(self.style.SUCCESS('\n[OK] Done!'))

    def _assign_equipment_icons(self, dry_run, force):
        """分配裝備圖示"""
        # 追蹤每種類型已使用的圖示索引
        type_counters = {
            'HELMET': 0,
            'ARMOR': 0,
            'BOOTS': 0,
            'TOOL': 0,
        }

        for equipment in Equipment.objects.all().order_by('id'):
            current_icon = equipment.icon

            # 如果已有圖示且不強制覆蓋，則跳過
            if current_icon and not force:
                self.stdout.write(f'  [OK] {equipment.name}: has icon ({current_icon})')
                continue

            # 先檢查名稱對應
            new_icon = self.EQUIPMENT_NAME_MAPPING.get(equipment.name)

            # 如果沒有名稱對應，則使用類型對應
            if not new_icon:
                eq_type = equipment.equipment_type
                # 處理 TOOL_* 類型
                if eq_type.startswith('TOOL'):
                    eq_type = 'TOOL'

                icons = self.EQUIPMENT_ICONS.get(eq_type, [])
                if icons:
                    idx = type_counters.get(eq_type, 0) % len(icons)
                    new_icon = icons[idx]
                    type_counters[eq_type] = idx + 1

            if new_icon:
                if not dry_run:
                    equipment.icon = new_icon
                    equipment.save(update_fields=['icon'])
                self.stdout.write(f'  + {equipment.name}: {new_icon}')
            else:
                self.stdout.write(self.style.WARNING(f'  [?] {equipment.name}: no icon available'))

    def _assign_item_icons(self, dry_run, force):
        """分配道具圖示（目前使用 Font Awesome 圖示，這裡只做說明）"""
        items = Item.objects.all()

        if not items.exists():
            self.stdout.write('  No item data')
            return

        self.stdout.write('  Items use Font Awesome icons (dynamic based on effect_type in template)')

        # 顯示效果類型對應的圖示
        effect_icons = {
            'HINT': 'fa-lightbulb',
            'HEAL': 'fa-heart',
            'REMOVE_OPTION': 'fa-times-circle',
            'SHIELD': 'fa-shield-alt',
            'TIME_EXTEND': 'fa-clock',
            'DISTRIBUTION': 'fa-chart-pie',
            'SKIP': 'fa-forward',
            'COMBO_PROTECT': 'fa-magic',
        }

        for item in items:
            icon = effect_icons.get(item.effect_type, 'fa-flask')
            self.stdout.write(f'  [OK] {item.name}: {icon}')
