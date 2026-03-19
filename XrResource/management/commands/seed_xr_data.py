from django.core.management.base import BaseCommand
from XrResource.models import EquipmentCategory, XrEquipment

class Command(BaseCommand):
    help = 'Seeds the database with initial XR and GoPro equipment data'

    def handle(self, *args, **options):
        # 1. Ensure Categories exist
        cats = {
            'computer': EquipmentCategory.objects.get_or_create(name='電腦', icon='fas fa-desktop')[0],
            'headset': EquipmentCategory.objects.get_or_create(name='頭盔', icon='fas fa-headset')[0],
            'host': EquipmentCategory.objects.get_or_create(name='主機', icon='fas fa-video')[0],
            'battery': EquipmentCategory.objects.get_or_create(name='電池', icon='fas fa-battery-full')[0],
            'sd_card': EquipmentCategory.objects.get_or_create(name='記憶卡', icon='fas fa-sd-card')[0],
            'others': EquipmentCategory.objects.get_or_create(name='其他配件', icon='fas fa-box')[0],
        }

        # 2. Add VR Data
        XrEquipment.objects.get_or_create(
            serial_number='VR-PC-01',
            defaults={
                'section': 'vr', 'category': cats['computer'], 'name': 'VR 高效能電腦 01',
                'specifications': 'Intel i9, RTX 4090, 64GB RAM', 'note': '位於 A 棟實驗室'
            }
        )
        XrEquipment.objects.get_or_create(
            serial_number='MQ3-001',
            defaults={
                'section': 'vr', 'category': cats['headset'], 'name': 'Meta Quest 3',
                'specifications': '128GB, 包含觸控手把', 'note': '新品'
            }
        )
        XrEquipment.objects.get_or_create(
            serial_number='BS-001',
            defaults={
                'section': 'vr', 'category': cats['others'], 'name': 'VR 基地台 (Base Station)',
                'specifications': 'V2.0', 'note': 'SteamVR 必備'
            }
        )

        # 3. Add GoPro Data
        XrEquipment.objects.get_or_create(
            serial_number='GP12-001',
            defaults={
                'section': 'gopro', 'category': cats['host'], 'name': 'GoPro Hero 12 Black',
                'specifications': '5.3K 影片, HDR', 'note': '常用主機'
            }
        )
        XrEquipment.objects.get_or_create(
            serial_number='GP-B-01',
            defaults={
                'section': 'gopro', 'category': cats['battery'], 'name': 'Enduro 高性能電池',
                'specifications': '1720mAh', 'note': '低溫環境優化'
            }
        )
        XrEquipment.objects.get_or_create(
            serial_number='SD-256-01',
            defaults={
                'section': 'gopro', 'category': cats['sd_card'], 'name': 'SanDisk Extreme 256GB',
                'specifications': 'V30, A2, 190MB/s', 'note': '4K 錄製建議'
            }
        )
        XrEquipment.objects.get_or_create(
            serial_number='GP-ACC-01',
            defaults={
                'section': 'gopro', 'category': cats['others'], 'name': '三向固定架 (3-Way 2.0)',
                'specifications': '自拍桿/三腳架/摺疊臂', 'note': '原廠配件'
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded XR data'))
