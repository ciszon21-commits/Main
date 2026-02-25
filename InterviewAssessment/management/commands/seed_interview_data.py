from django.core.management.base import BaseCommand
from InterviewAssessment.models import QuestionCategory, Question

class Command(BaseCommand):
    help = 'Seeds expanded interview questions for Character, Digital Talent, and Information Security'

    def handle(self, *args, **options):
        # 1. Create Categories
        cat_character, _ = QuestionCategory.objects.get_or_create(
            name='品格選才',
            defaults={'description': '評估候選人的品格、職業道德與價值觀'}
        )
        cat_digital, _ = QuestionCategory.objects.get_or_create(
            name='數位育才',
            defaults={'description': '評估候選人的數位能力、邏輯思維與技術潛力'}
        )
        cat_infosec, _ = QuestionCategory.objects.get_or_create(
            name='資訊安全',
            defaults={'description': '評估候選人的資安意識與防護觀念'}
        )

        # 2. Expanded Character Questions (SJT/Ethics)
        char_questions = [
            # Existing
            {
                'text': '當你在工作中發現一個錯誤，但沒有人注意到，你會怎麼做？',
                'type': 'single',
                'choices': ['假裝沒看到', '私下修正但不告訴主管', '主動報告並提出解決方案', '如果是小錯誤就忽略'],
                'correct': '主動報告並提出解決方案',
                'points': 10
            },
            {
                'text': '團隊合作中，如果同事進度落後影響到你的工作，你會？',
                'type': 'single',
                'choices': ['向主管抱怨', '主動協助同事並溝通協調', '只做自己的部分', '要求更換隊友'],
                'correct': '主動協助同事並溝通協調',
                'points': 10
            },
            # ... Previous SJT questions ...
            {
                'text': '【情境題】您發現專案中使用與現況不符的數據，若修正將導致各項進度延期，若不修正則可能影響長期品質但無立即危險。您會如何處理？',
                'type': 'single',
                'choices': [
                    '私下微調數據使其看起來合理，不影響進度',
                    '向專案經理報告風險，並共同制定透明的解決方案',
                    '自行修正並提交報告，不讓主管操心延期問題',
                    '保持原樣提交，因為目前沒有立即危險'
                ],
                'correct': '向專案經理報告風險，並共同制定透明的解決方案',
                'points': 15
            },
            {
                'text': '【情境題】團隊中兩位成員對設計方向有嚴重分歧，導致進度停滯。身為團隊成員，您會？',
                'type': 'single',
                'choices': [
                    '不介入，等待主管裁決',
                    '支持較強勢的一方以盡快結束爭論',
                    '建議雙方列出優缺點進行客觀分析，協助尋求共識',
                    '私下勸退其中一人'
                ],
                'correct': '建議雙方列出優缺點進行客觀分析，協助尋求共識',
                'points': 15
            },
            {
                'text': '【情境題】您注意到一位資深同事經常便宜行事，違反公司的標準作業程序(SOP)，雖然目前未出錯，但您認為有潛在風險。您會？',
                'type': 'single',
                'choices': [
                    '這是資深同事的經驗，不予置評',
                    '在公開會議上直接指正他',
                    '私下婉轉提醒他可能的風險，若無改善則向主管反映',
                    '雖然不認同，但跟著他做以融入團隊'
                ],
                'correct': '私下婉轉提醒他可能的風險，若無改善則向主管反映',
                'points': 15
            },
            {
                'text': '對於「持續學習」這件事，您的看法是？',
                'type': 'single',
                'choices': [
                    '工作以後就不需要讀書了，經驗比較重要',
                    '有空閒時才需要學習新技術',
                    '為了升遷才需要考證照',
                    '主動關注產業趨勢，定期學習新技能以貢獻團隊'
                ],
                'correct': '主動關注產業趨勢，定期學習新技能以貢獻團隊',
                'points': 10
            }
        ]

        for q_data in char_questions:
            Question.objects.get_or_create(
                category=cat_character,
                text=q_data['text'],
                defaults={
                    'question_type': q_data['type'],
                    'choices': q_data['choices'],
                    'correct_answer': q_data['correct'],
                    'points': q_data['points']
                }
            )

        # 3. Expanded Digital Questions (BIM/IT)
        digital_questions = [
            # Existing
            {
                'text': '下列哪一種不屬於常見的雲端服務模式？',
                'type': 'single',
                'choices': ['IaaS', 'PaaS', 'SaaS', 'TaaS'],
                'correct': 'TaaS',
                'points': 10
            },
             {
                'text': 'Python 中用於資料處理的常用函式庫是？',
                'type': 'single',
                'choices': ['Pandas', 'Requests', 'Flask', 'Django'],
                'correct': 'Pandas',
                'points': 10
            },
            # New BIM / Engineering IT
            {
                'text': '在 BIM (建築資訊模型) 中，"LOD" 代表什麼意義？',
                'type': 'single',
                'choices': [
                    'Level of Design (設計等級)',
                    'Level of Detail (細節等級 - 圖形)',
                    'Level of Development (發展等級 - 幾何與資訊)',
                    'Layers of Data (數據層級)'
                ],
                'correct': 'Level of Development (發展等級 - 幾何與資訊)',
                'points': 10
            },
            {
                'text': '下列何者是「碰撞檢測 (Clash Detection)」的主要目的？',
                'type': 'single',
                'choices': [
                    '檢查建築外觀美感是否衝突',
                    '在施工前發現建築、結構、機電系統間的空間衝突',
                    '計算建築物的能源消耗',
                    '檢查結構強度是否足夠'
                ],
                'correct': '在施工前發現建築、結構、機電系統間的空間衝突',
                'points': 10
            },
            {
                'text': '關於 CDE (Common Data Environment) 通用資料環境，下列敘述何者正確？',
                'type': 'single',
                'choices': [
                    '只是一個用來存軟體授權的地方',
                    '是所有專案資訊的單一資料來源，用於跨團隊協作與管理',
                    '是用來進行 VR 導覽的環境',
                    '是專門用來備份資料的硬碟'
                ],
                'correct': '是所有專案資訊的單一資料來源，用於跨團隊協作與管理',
                'points': 10
            },
            {
                'text': 'BIM 國際標準 ISO 19650 主要規範什麼內容？',
                'type': 'single',
                'choices': [
                    '資訊安全管理 (Information Security)',
                    '環境管理系統 (Environmental Management)',
                    '建築資訊模型的資訊管理 (Information Management using BIM)',
                    '品質管理系統 (Quality Management)'
                ],
                'correct': '建築資訊模型的資訊管理 (Information Management using BIM)',
                'points': 10
            },
            {
                'text': '所謂 5D BIM 通常是指在模型中加入了什麼資訊？',
                'type': 'single',
                'choices': [
                    '時間 (排程)',
                    '成本 (預算)',
                    '永續性 (能源分析)',
                    '設施管理 (維運)'
                ],
                'correct': '成本 (預算)',
                'points': 10
            }
        ]

        for q_data in digital_questions:
            Question.objects.get_or_create(
                category=cat_digital,
                text=q_data['text'],
                defaults={
                    'question_type': q_data['type'],
                    'choices': q_data['choices'],
                    'correct_answer': q_data['correct'],
                    'points': q_data['points']
                }
            )

        # 4. Information Security Questions
        infosec_questions = [
            {
                'text': '「社交工程 (Social Engineering)」攻擊手法主要是利用什麼弱點？',
                'type': 'single',
                'choices': [
                    '電腦系統的漏洞',
                    '網路防火牆的設定錯誤',
                    '人類的心理弱點與信任',
                    '加密演算法的缺陷'
                ],
                'correct': '人類的心理弱點與信任',
                'points': 10
            },
            {
                'text': '收到一封看似來自主管的緊急 Email，要求您立即匯款或提供密碼，您應該？',
                'type': 'single',
                'choices': [
                    '遵照指示立即行動，以免耽誤公事',
                    '回信詢問確認',
                    '透過電話或當面與主管確認',
                    '轉寄給其他同事詢問意見'
                ],
                'correct': '透過電話或當面與主管確認',
                'points': 10
            },
            {
                'text': '關於密碼設定，下列何者是較安全的做法？',
                'type': 'single',
                'choices': [
                    '使用生日或電話號碼方便記憶',
                    '所有網站都使用同一組密碼',
                    '使用包含大小寫字母、數字及符號的長密碼，並定期更換',
                    '將密碼寫在便利貼上貼在螢幕旁'
                ],
                'correct': '使用包含大小寫字母、數字及符號的長密碼，並定期更換',
                'points': 10
            },
            {
                'text': '如果不小心點擊了疑似釣魚郵件的連結，第一步應該做什麼？',
                'type': 'single',
                'choices': [
                    '立即關機並拔掉電源',
                    '假裝沒發生過，繼續工作',
                    '立即斷開網路並通報資訊部門 (IT/MIS)',
                    '自行下載免費防毒軟體掃描'
                ],
                'correct': '立即斷開網路並通報資訊部門 (IT/MIS)',
                'points': 10
            },
            {
                'text': '在資訊安全領域中，CIA 三要素是指？',
                'type': 'single',
                'choices': [
                    'Confidentiality (機密性), Integrity (完整性), Availability (可用性)',
                    'Cybersecurity (網路安全), Intelligence (情報), Authentication (驗證)',
                    'Cost (成本), Insurance (保險), Audit (稽核)',
                    'Cloud (雲端), Internet (網路), Access (存取)'
                ],
                'correct': 'Confidentiality (機密性), Integrity (完整性), Availability (可用性)',
                'points': 10
            }
        ]

        for q_data in infosec_questions:
            Question.objects.get_or_create(
                category=cat_infosec,
                text=q_data['text'],
                defaults={
                    'question_type': q_data['type'],
                    'choices': q_data['choices'],
                    'correct_answer': q_data['correct'],
                    'points': q_data['points']
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded expanded questions including InfoSec.'))
