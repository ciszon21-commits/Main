from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from BidQA.models import Bid, Committee, BidCommittee, Question
import datetime
import random

class Command(BaseCommand):
    help = '為 BidQA 建立專業的測試資料'

    def handle(self, *args, **options):
        # 取得使用者
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('找不到使用者，請先建立超級使用者'))
            return

        self.stdout.write('清理現有測試資料...')
        Bid.objects.all().delete()
        Committee.objects.all().delete()

        # 1. 建立專業委員
        committees_data = [
            {'name': '王大明', 'organization': '行政院交通部', 'specialty': '土木工程、交通規劃', 'notes': '資深工程審查委員'},
            {'name': '林志成', 'organization': '台北大學土木系', 'specialty': '結構技師、防災工程', 'notes': '專攻橋樑安全監測'},
            {'name': '陳美玲', 'organization': '環保署環境監測中心', 'specialty': '環境工程、ESG評估', 'notes': '具有多項環保標章審核經驗'},
            {'name': '張坤山', 'organization': '中興工程顧問', 'specialty': '電機工程、自動化系統', 'notes': '曾參與多項重大國家建設'},
            {'name': '黃曉芳', 'organization': '法律扶助基金會', 'specialty': '營建法規、採購案件', 'notes': '專攻標案合約法律風險控管'},
            {'name': '李建德', 'organization': '工研院綠能所', 'specialty': '能源工程、太陽能系統', 'notes': '國家綠能政策諮詢顧問'},
        ]

        committees = []
        for data in committees_data:
            c = Committee.objects.create(**data)
            committees.append(c)

        # 2. 建立專業標案
        bids_data = [
            {
                'name': '2024年度智慧交通網路流量監測系統提升計畫',
                'bid_number': 'TR-2024-001',
                'bid_date': datetime.date(2024, 3, 15),
                'status': 'won',
                'description': '本計畫旨在透過 AI 視覺辨識與大數據分析，優化都會區路口車流監測，並與導航系統連動以降低塞車率。'
            },
            {
                'name': '綠色能源示範園區太陽能板設置與維護採購案',
                'bid_number': 'GE-2024-102',
                'bid_date': datetime.date(2024, 5, 20),
                'status': 'unannounced',
                'description': '於科學園區內設置高效能太陽能發電設施，預計佔地 5 公頃，包含後續 10 年之運護管理。'
            },
            {
                'name': '國家圖書館南部分館數位化典藏設備採購',
                'bid_number': 'NL-2024-055',
                'bid_date': datetime.date(2023, 12, 10),
                'status': 'lost',
                'description': '採購高解析度扫描儀與伺服器架構，對珍貴歷史古蹟文件進行數位典藏工作。'
            },
            {
                'name': '台中港區自動化裝卸設施改進工程',
                'bid_number': 'PH-2024-210',
                'bid_date': datetime.date(2024, 1, 30),
                'status': 'failed',
                'description': '針對現有碼頭裝卸設施進行自動化升級，因為投標商過少（僅一家）而導致流標。'
            }
        ]

        q_a_pool = [
            {
                'q': '關於系統之資訊安全，是否具備完整的滲透測試報告與防護機制？',
                'a': '本系統符合 ISO 27001 標準，在出廠前已進行完整的漏洞掃描，並提供 24/7 的監控機制。',
                'ref': '參考服務建議書第 45 頁、資安防護規範文件。'
            },
            {
                'q': '本工程之施工進度若因不可抗力因素延宕，是否有相關的備援方案？',
                'a': '我們已擬定應變計畫，包含人力彈性分配與階段性交付。若遇豪雨等天氣，會優先進行室內組裝作業。',
                'ref': '參考工程進度計畫表 (附件三)。'
            },
            {
                'q': '計畫書中提到的 ESG 績效評估指標，具體涵蓋哪些項目？',
                'a': '涵蓋碳足跡計算、廢棄物減量比率以及在地供應商合作比例，符合政府推行之永續採購準則。',
                'ref': 'ESG 永續發展承諾書。'
            },
            {
                'q': '對於後續 10 年的維修零件備料，投標廠商如何保證供應穩定？',
                'a': '我們與原廠簽訂了長期供應合約，並在本地倉儲備有核心組件至少兩年之消耗量，確保即時更換。',
                'ref': '零部件供應鏈協議影本。'
            }
        ]

        for b_data in bids_data:
            bid = Bid.objects.create(created_by=user, **b_data)
            
            # 隨機分配 3-5 位委員
            selected_committees = random.sample(committees, random.randint(3, 5))
            for committee in selected_committees:
                bc = BidCommittee.objects.create(bid=bid, committee=committee)
                
                # 每個委員隨機 1-2 個問題
                for i in range(random.randint(1, 2)):
                    qa = random.choice(q_a_pool)
                    Question.objects.create(
                        bid_committee=bc,
                        question=qa['q'],
                        answer=qa['a'],
                        reference=qa['ref'],
                        order=i
                    )

        self.stdout.write(self.style.SUCCESS('成功建立專業測試資料！'))
