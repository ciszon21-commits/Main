import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Equipment

print("開始更新裝備圖標...")

Equipment.objects.filter(equipment_type='HELMET').update(icon='rpg/equipment_icons/helmet.png')
print("✅ 已更新頭盔圖標")

Equipment.objects.filter(equipment_type='ARMOR').update(icon='rpg/equipment_icons/vest.png')
print("✅ 已更新護甲圖標")

Equipment.objects.filter(equipment_type='BOOTS').update(icon='rpg/equipment_icons/boots.png')
print("✅ 已更新靴子圖標")

Equipment.objects.filter(equipment_type='TOOL_UAV').update(icon='rpg/equipment_icons/uav.png')
print("✅ 已更新無人機圖標")

Equipment.objects.filter(equipment_type='TOOL_CAMERA').update(icon='rpg/equipment_icons/camera360.png')
print("✅ 已更新環景相機圖標")

Equipment.objects.filter(equipment_type='TOOL_GLASSES').update(icon='rpg/equipment_icons/smart_glasses.png')
print("✅ 已更新智慧眼鏡圖標")

Equipment.objects.filter(equipment_type='TOOL_APP').update(icon='rpg/equipment_icons/inspection_app.png')
print("✅ 已更新查驗APP圖標")

print('\n🎉 完成！所有裝備圖標已更新！')
