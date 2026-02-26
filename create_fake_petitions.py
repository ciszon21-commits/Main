"""建立 2 筆有 50 個附議的假提議資料"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from LHAWish.models import Petition, Endorsement

# 取得提議人
proposer = User.objects.first()
print(f'使用提議人: {proposer.username}')

# 建立 50 個假 user
fake_users = []
for i in range(1, 51):
    u, created = User.objects.get_or_create(
        username=f'fakeuser_{i:03d}',
        defaults={
            'first_name': f'測試{i}',
            'last_name': '員工',
            'email': f'fake{i}@test.com',
            'is_active': True,
        }
    )
    fake_users.append(u)
    if created:
        u.set_password('test1234')
        u.save()

print(f'已準備 {len(fake_users)} 個假使用者')

# 建立 2 筆提議
p1 = Petition.objects.create(
    title='建議增設員工休息室與紓壓空間',
    content='<p>目前辦公環境缺乏休息空間，建議在各樓層設置小型休息室，配備舒適沙發、飲水機及簡易茶水區，讓同仁在工作疲憊時可以短暫休息，提升工作效率與身心健康。</p><p>具體建議：</p><ul><li>每層樓設置至少一間 10 坪休息室</li><li>配備沙發、按摩椅各 2 張</li><li>設置簡易茶水吧台</li></ul>',
    proposer=proposer,
    assigned_group='management',
    status='endorsing',
    endorsement_threshold=50,
)

p2 = Petition.objects.create(
    title='推動每週一日彈性居家辦公制度',
    content='<p>為因應現代工作型態的轉變，建議部門推動「每週一日彈性居家辦公」制度，讓同仁可自行選擇一天在家辦公。</p><p>預期效益：</p><ul><li>減少通勤時間，提高生活品質</li><li>降低辦公室空間壓力</li><li>提升工作自主性與滿意度</li><li>參考其他機關已實施案例，生產力不降反升</li></ul>',
    proposer=proposer,
    assigned_group='management',
    status='endorsing',
    endorsement_threshold=50,
)

print(f'已建立提議 1: {p1.title} (pk={p1.pk})')
print(f'已建立提議 2: {p2.title} (pk={p2.pk})')

# 為每筆提議加入 50 個附議
for p in [p1, p2]:
    for u in fake_users:
        Endorsement.objects.get_or_create(petition=p, user=u)
    print(f'  提議 "{p.title}" 附議數: {p.endorsement_count}')

print('完成！')
