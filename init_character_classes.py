"""
初始化 CharacterClass 資料
"""
from EngineerRPG.models import CharacterClass

# 建立三個職業
classes_data = [
    {
        'code': 'CIVIL',
        'name': '土木戰士 (Civil Warrior)',
        'description': '精通結構設計與施工管理的專業工程師,擅長土木工程領域的各項挑戰。',
        'base_hp': 60,
        'base_mp': 100,
    },
    {
        'code': 'ME',
        'name': '機電法師 (M&E Mage)',
        'description': '掌握機電系統與能源管理的技術專家,專注於機電整合與智慧控制。',
        'base_hp': 50,
        'base_mp': 120,
    },
    {
        'code': 'SAFETY',
        'name': '職安僧侶 (Safety Monk)',
        'description': '精通職安衛法規與風險評估的安全守護者,致力於工地安全與防災。',
        'base_hp': 55,
        'base_mp': 110,
    },
]

for data in classes_data:
    CharacterClass.objects.get_or_create(
        code=data['code'],
        defaults={
            'name': data['name'],
            'description': data['description'],
            'base_hp': data['base_hp'],
            'base_mp': data['base_mp'],
        }
    )

print("CharacterClass 初始化完成!")
print(f"總共有 {CharacterClass.objects.count()} 個職業")
for cls in CharacterClass.objects.all():
    print(f"  - {cls.code}: {cls.name}")
