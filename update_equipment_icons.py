"""
更新裝備圖標的管理腳本
使用方法：python manage.py shell < update_equipment_icons.py
"""

from EngineerRPG.models import Equipment

# 裝備圖標映射
icon_mapping = {
    'HELMET': 'rpg/equipment_icons/helmet.png',
    'ARMOR': 'rpg/equipment_icons/vest.png',
    'BOOTS': 'rpg/equipment_icons/boots.png',
    'TOOL_UAV': 'rpg/equipment_icons/uav.png',
    'TOOL_CAMERA': 'rpg/equipment_icons/camera360.png',
    'TOOL_GLASSES': 'rpg/equipment_icons/smart_glasses.png',
    'TOOL_APP': 'rpg/equipment_icons/inspection_app.png',
}

print("開始更新裝備圖標...")

updated_count = 0
for equipment_type, icon_path in icon_mapping.items():
    equipments = Equipment.objects.filter(equipment_type=equipment_type)
    count = equipments.count()
    
    if count > 0:
        equipments.update(icon=icon_path)
        print(f"✅ 已更新 {count} 個 {equipment_type} 類型的裝備圖標")
        updated_count += count
    else:
        print(f"⚠️  找不到 {equipment_type} 類型的裝備")

print(f"\n總共更新了 {updated_count} 個裝備的圖標！")
print("完成！")
