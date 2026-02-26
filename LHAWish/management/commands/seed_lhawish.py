from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from LHAWish.models import Post, Petition, Endorsement, PetitionComment, Comment
from django.utils import timezone
import random


class Command(BaseCommand):
    help = '產生 LHAWish 假資料（園路願望 + 研發專案）'

    def handle(self, *args, **options):
        # 確保至少有一個使用者
        users = list(User.objects.all())
        if len(users) < 2:
            for i in range(3):
                u, _ = User.objects.get_or_create(
                    username=f'testuser{i+1}',
                    defaults={
                        'first_name': ['小明', '小華', '小美'][i],
                        'last_name': ['王', '李', '陳'][i],
                    }
                )
                u.set_password('test1234')
                u.save()
            users = list(User.objects.all())

        self.stdout.write('=== 開始產生假資料 ===')

        # ---------- 園路願望 ----------
        petitions_data = [
            {
                'title': '建議增設員工休息室',
                'content': '<p>目前部門內缺乏一個可以讓同仁短暫休息、放鬆的空間。建議在 B 棟 3 樓空置的會議室改建為員工休息室，配備沙發、飲水機和簡易茶水設施。</p><p>這樣可以提升同仁的工作效率和幸福感。</p>',
                'assigned_group': 'management',
                'status': 'endorsing',
                'threshold': 50,
            },
            {
                'title': '希望每週三下午舉辦部門運動時間',
                'content': '<p>久坐辦公容易導致頸椎和腰椎問題。建議每週三下午 4:00-5:00 安排部門團體運動時間，如：</p><ul><li>羽球</li><li>瑜珈伸展</li><li>快走/慢跑</li></ul><p>既能增進同仁感情，又能維護健康。</p>',
                'assigned_group': 'management',
                'status': 'endorsing',
                'threshold': 50,
            },
            {
                'title': '建議採購站立式辦公桌',
                'content': '<p>長時間坐在辦公桌前工作對身體不好，建議部門採購 <strong>5-10 張可調整高度的站立式辦公桌</strong>，讓有需求的同仁可以交替使用。</p><p>市場上有許多平價的升降桌，預算約 $3,000-5,000/張。</p>',
                'assigned_group': 'engineering',
                'status': 'established',
                'threshold': 30,
            },
            {
                'title': '園區路燈照明不足需改善',
                'content': '<p>下班時間園區內多處路段照明不足，尤其是 C 棟到停車場之間的步道，存在安全隱患。</p><p>建議增設 LED 路燈，或是替換現有較暗的燈泡。</p>',
                'assigned_group': 'engineering',
                'status': 'endorsing',
                'threshold': 50,
            },
            {
                'title': '建議實施彈性上下班制度',
                'content': '<p>目前固定的上下班時間（8:00-17:00）對於需要接送小孩的同仁來說不太方便。建議改為彈性工時制度：</p><ul><li>核心時間：10:00-15:00 必須在崗</li><li>彈性時間：7:00-10:00 / 15:00-19:00 自由選擇</li></ul><p>只要每天滿 8 小時即可。</p>',
                'assigned_group': 'management',
                'status': 'endorsing',
                'threshold': 50,
            },
            {
                'title': '希望改善茶水間設備',
                'content': '<p>茶水間的微波爐已使用超過 5 年，經常故障。冰箱也不夠大，中午帶便當的同仁放不下。</p><p>建議更新以下設備：</p><ul><li>新微波爐 x2</li><li>大型冰箱 x1</li><li>淨水器保養</li></ul>',
                'assigned_group': 'other',
                'status': 'responded',
                'threshold': 30,
            },
            {
                'title': '建議增加教育訓練補助',
                'content': '<p>希望部門能提供更多專業技能的教育訓練機會和補助，包括：</p><ul><li>線上課程平台年費補助（如 Udemy、Coursera）</li><li>外部研討會參加費用</li><li>專業證照考試費用</li></ul><p>這有助於提升團隊整體技術能力。</p>',
                'assigned_group': 'management',
                'status': 'endorsing',
                'threshold': 50,
            },
            {
                'title': '停車場車位不足問題',
                'content': '<p>每天早上 8:30 以後停車場就已經客滿，很多同仁只能停到很遠的地方。建議：</p><ol><li>評估是否可增設臨時停車區</li><li>推動共乘制度</li><li>提供搭乘公車交通補助</li></ol>',
                'assigned_group': 'engineering',
                'status': 'endorsing',
                'threshold': 50,
            },
        ]

        for i, pd in enumerate(petitions_data):
            proposer = random.choice(users)
            p, created = Petition.objects.get_or_create(
                title=pd['title'],
                defaults={
                    'content': pd['content'],
                    'proposer': proposer,
                    'assigned_group': pd['assigned_group'],
                    'status': pd['status'],
                    'endorsement_threshold': pd['threshold'],
                }
            )
            if created:
                # 隨機添加附議
                endorsement_count = random.randint(3, pd['threshold'])
                endorsers = random.sample(users, min(len(users), endorsement_count))
                for u in endorsers:
                    Endorsement.objects.get_or_create(petition=p, user=u)

                # 隨機添加留言
                comments = [
                    '支持這個提議！', '好想法，希望能盡快實施。', '這確實是大家的心聲。',
                    '很棒的建議，我也有同感。', '+1', '完全同意！',
                    '有沒有考慮過預算問題？', '我覺得可以先試辦看看。',
                ]
                for _ in range(random.randint(1, 5)):
                    PetitionComment.objects.create(
                        petition=p,
                        author=random.choice(users),
                        content=random.choice(comments),
                    )

                if pd['status'] == 'established' and not p.deadline:
                    p.deadline = timezone.now() + timezone.timedelta(days=60)
                    p.save()

                if pd['status'] == 'responded':
                    p.response_content = '感謝提議，我們已經著手改善。預計下個月完成設備更新。'
                    p.response_at = timezone.now()
                    p.response_by = users[0]
                    p.save()

                self.stdout.write(f'  ✓ 園路願望: {p.title}')

        # ---------- 研發專案 ----------
        rnd_data = [
            {
                'title': 'Excel 匯出報表格式跑掉',
                'content': '<p>使用「查詢結果匯出 Excel」功能時，日期欄位格式顯示不正確，變成數字序號而非日期格式。</p><p>影響範圍：所有包含日期欄位的報表。</p>',
                'category': 'bug',
                'priority': 'high',
                'status': 'pending',
                'package_name': '報表模組',
                'problem_type': '格式異常',
            },
            {
                'title': '新增批次上傳功能',
                'content': '<p>目前資料只能逐筆輸入，建議新增 <strong>Excel 批次上傳</strong>功能。使用者可以下載範本、填入資料後一次匯入。</p><p>預計可大幅提升資料建置效率。</p>',
                'category': 'feature',
                'priority': 'normal',
                'status': 'scheduled',
                'package_name': '資料管理',
                'problem_type': '',
            },
            {
                'title': '登入頁面 RWD 在手機上跑版',
                'content': '<p>在手機（iPhone 15 / Samsung S24）上開啟登入頁面時，輸入框和按鈕會超出螢幕寬度。需要調整 CSS 的 media query。</p>',
                'category': 'bug',
                'priority': 'normal',
                'status': 'in_progress',
                'package_name': '前端',
                'problem_type': 'UI 異常',
            },
            {
                'title': '系統效能優化——首頁載入過慢',
                'content': '<p>首頁載入時間超過 5 秒，主因是 Dashboard 查詢了過多資料。建議方案：</p><ul><li>加入分頁機制</li><li>使用 Redis 快取</li><li>優化 SQL 查詢（N+1 問題）</li></ul>',
                'category': 'feature',
                'priority': 'high',
                'status': 'pending',
                'package_name': '系統核心',
                'problem_type': '效能問題',
            },
            {
                'title': 'API 回應 500 錯誤',
                'content': '<p>呼叫 <code>/api/v1/reports/</code> 時偶爾會回傳 500 Internal Server Error。從 log 看是 NoneType 錯誤，需追查原因。</p>',
                'category': 'bug',
                'priority': 'critical',
                'status': 'pending',
                'package_name': 'API',
                'problem_type': '後端錯誤',
            },
            {
                'title': '新增暗色主題（Dark Mode）',
                'content': '<p>建議系統支援暗色模式，方便夜間或光線較暗環境下使用。可以參考 GitHub 的暗色主題設計。</p>',
                'category': 'feature',
                'priority': 'low',
                'status': 'pending',
                'package_name': '前端',
                'problem_type': '',
            },
        ]

        for rd in rnd_data:
            author = random.choice(users)
            post, created = Post.objects.get_or_create(
                title=rd['title'],
                type='rnd',
                defaults={
                    'content': rd['content'],
                    'author': author,
                    'category': rd['category'],
                    'priority': rd['priority'],
                    'status': rd['status'],
                    'package_name': rd.get('package_name', ''),
                    'problem_type': rd.get('problem_type', ''),
                }
            )
            if created:
                # 隨機留言
                dev_comments = [
                    '我來看一下這個問題。', '已重現，正在修復中。',
                    '建議排到下個 sprint。', '需要更多資訊才能判斷。',
                    '這個功能+1', '優先度建議提高。',
                ]
                for _ in range(random.randint(0, 3)):
                    Comment.objects.create(
                        post=post,
                        author=random.choice(users),
                        content=random.choice(dev_comments),
                    )
                self.stdout.write(f'  ✓ 研發專案: {post.title}')

        self.stdout.write(self.style.SUCCESS('\n=== 假資料產生完成！==='))
        self.stdout.write(f'  園路願望: {Petition.objects.count()} 筆')
        self.stdout.write(f'  研發專案: {Post.objects.filter(type="rnd").count()} 筆')
