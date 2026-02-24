"""
初始化完整技能樹資料 V2.0
──────────────────────────────────────────
從 db.sqlite3 中匯出的實際資料重新建置
座標已採用像素座標（150px grid）
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from EngineerRPG.models import CharacterClass, SkillNode, Course, Equipment


class Command(BaseCommand):
    help = '初始化完整技能樹和課程資料 (V2.0)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('開始初始化完整技能樹資料 V2.0...'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        try:
            civil  = CharacterClass.objects.get(code='CIVIL')
            me     = CharacterClass.objects.get(code='ME')
            safety = CharacterClass.objects.get(code='SAFETY')
        except CharacterClass.DoesNotExist:
            self.stdout.write(self.style.ERROR('請先執行 init_rpg_data 創建職業資料'))
            return

        with transaction.atomic():
            self.stdout.write('清除舊技能樹資料...')
            SkillNode.objects.all().delete()
            Course.objects.all().delete()

            # ═══════════════════════════════════════
            # 共同必修 (ROOT / 通用)
            # ═══════════════════════════════════════
            self.stdout.write('\n📚 創建共同必修...')

            novice_1 = SkillNode.objects.create(
                name='監造行政作業基礎',
                description='學習監造工程師的基本行政作業，包括文件管理、報表填寫、會議記錄等基礎技能。',
                node_type='ROOT', character_class=None,
                exp_reward=686, position_x=100, position_y=0,
            )
            novice_2 = SkillNode.objects.create(
                name='工程法規概論',
                description='了解工程相關基本法規，包括建築法、政府採購法、契約管理等基礎知識。',
                node_type='ROOT', character_class=None,
                exp_reward=736, position_x=250, position_y=0,
            )
            novice_3 = SkillNode.objects.create(
                name='工地安全衛生基礎',
                description='學習工地基本安全規範，包括個人防護具使用、危險辨識、緊急應變等。',
                node_type='ROOT', character_class=None,
                exp_reward=736, position_x=400, position_y=0,
            )

            Course.objects.create(
                title='新進監造工程師訓練',
                description='新人必修的基礎訓練課程，涵蓋行政作業、法規與安全。',
                content_type='VIDEO',
                content_url='https://example.com/novice-training',
                duration_minutes=180,
            ).skill_nodes.add(novice_1, novice_2, novice_3)

            # ═══════════════════════════════════════
            # 土木戰士 (Civil Warrior) — 完整樹
            # ═══════════════════════════════════════
            self.stdout.write('\n⚔️  創建土木戰士技能樹...')

            # ── Row 0 (y=0) 額外職業節點 ──
            civil_foundation = SkillNode.objects.create(
                name='基礎與支撐工程',
                description='連續壁、排樁、地下水觀測',
                node_type='CORE', character_class=civil,
                exp_reward=23570, position_x=550, position_y=0,
            )
            civil_pmis1 = SkillNode.objects.create(
                name='PMIS初階',
                description='',
                node_type='ROOT', character_class=civil,
                exp_reward=736, position_x=700, position_y=0,
            )
            civil_ethics = SkillNode.objects.create(
                name='監造權責與倫理',
                description='監造契約權責劃分、工程倫理與防貪指引、監造計畫書審查重點',
                node_type='ROOT', character_class=civil,
                exp_reward=135, position_x=850, position_y=0,
            )
            civil_vr = SkillNode.objects.create(
                name='VR虛擬實境訓練',
                description='解鎖VR眼鏡',
                node_type='ADVANCED', character_class=civil,
                exp_reward=50, position_x=1000, position_y=0,
            )

            # ── Row 1 (y=200) ──
            civil_1_1 = SkillNode.objects.create(
                name='鋼筋綁紮與查驗實務',
                description='學習鋼筋加工、綁紮、間距查驗等實務技術，確保結構安全。',
                node_type='CORE', character_class=civil,
                exp_reward=23570, position_x=100, position_y=200,
            )
            civil_1_1.parent_skills.add(novice_1, novice_2)

            civil_pmis2 = SkillNode.objects.create(
                name='PMIS中階',
                description='',
                node_type='ROOT', character_class=civil,
                exp_reward=736, position_x=250, position_y=200,
            )
            civil_pmis2.parent_skills.add(civil_pmis1)

            # ── Row 2 (y=400) ──
            civil_pmis3 = SkillNode.objects.create(
                name='PMIS高階',
                description='',
                node_type='ROOT', character_class=civil,
                exp_reward=735, position_x=100, position_y=400,
            )
            civil_pmis3.parent_skills.add(civil_pmis2)

            # ── Row 3 (y=600) ──
            civil_1_key = SkillNode.objects.create(
                name='數位測繪概論 (GIS)',
                description='【關鍵課程】學習 GIS 與數位測繪技術，解鎖「數位查驗 APP」工具。',
                node_type='CORE', character_class=civil,
                exp_reward=23620, position_x=100, position_y=600,
            )
            civil_1_key.parent_skills.add(novice_1, novice_2, novice_3, civil_pmis3)

            # ── Row 4 (y=800) ──
            civil_2_1 = SkillNode.objects.create(
                name='連續壁與深開挖監測',
                description='學習連續壁施工技術與深開挖監測系統。',
                node_type='CORE', character_class=civil,
                exp_reward=1, position_x=100, position_y=800,
            )
            civil_2_1.parent_skills.add(civil_1_key)

            civil_2_2 = SkillNode.objects.create(
                name='結構補強技術',
                description='掌握既有結構補強設計與施工技術。',
                node_type='CORE', character_class=civil,
                exp_reward=23620, position_x=250, position_y=800,
            )
            civil_2_2.parent_skills.add(civil_1_key)

            # ── Row 5 (y=1000) ──
            civil_2_key1 = SkillNode.objects.create(
                name='無人機操作證照',
                description='【關鍵課程】取得無人機操作證照，解鎖「UAV 無人機」工具。',
                node_type='ADVANCED', character_class=civil,
                exp_reward=200, position_x=100, position_y=1000,
            )
            civil_2_key1.parent_skills.add(civil_2_1, civil_2_2)

            # ── Row 6 (y=1200) ──
            civil_2_key2 = SkillNode.objects.create(
                name='3D 點雲處理技術',
                description='【關鍵課程】學習 3D 點雲資料處理與分析技術。',
                node_type='ADVANCED', character_class=civil,
                exp_reward=200, position_x=100, position_y=1200,
            )
            civil_2_key2.parent_skills.add(civil_2_key1)

            # ── Row 7 (y=1400) ──
            civil_3_1 = SkillNode.objects.create(
                name='專案成本控制與估驗',
                description='學習工程專案成本控制與估驗計價實務。',
                node_type='ADVANCED', character_class=civil,
                exp_reward=250, position_x=100, position_y=1400,
            )
            civil_3_1.parent_skills.add(civil_2_key1, civil_2_key2)

            civil_3_2 = SkillNode.objects.create(
                name='鄰損糾紛處理實務',
                description='掌握施工鄰損預防、鑑定與糾紛處理技巧。',
                node_type='ADVANCED', character_class=civil,
                exp_reward=250, position_x=250, position_y=1400,
            )
            civil_3_2.parent_skills.add(civil_2_key1, civil_2_key2)

            # ── Row 8 (y=1600) ──
            civil_3_key = SkillNode.objects.create(
                name='環景攝影技術',
                description='【關鍵課程】學習 360° 環景攝影技術，解鎖「環景相機」工具。',
                node_type='ADVANCED', character_class=civil,
                exp_reward=300, position_x=100, position_y=1600,
            )
            civil_3_key.parent_skills.add(civil_3_1, civil_3_2)

            # ═══════════════════════════════════════
            # 機電法師 (M&E Mage)
            # x 偏移 = 500（與共通節點區隔開）
            # ═══════════════════════════════════════
            self.stdout.write('\n🔮 創建機電法師技能樹...')
            MX = 500  # X offset

            me_1_1 = SkillNode.objects.create(
                name='給排水管路配置與試壓',
                description='學習給排水系統設計、管路配置與試壓測試技術。',
                node_type='CORE', character_class=me,
                exp_reward=100, position_x=MX, position_y=200,
            )
            me_1_1.parent_skills.add(novice_1, novice_2)

            me_1_2 = SkillNode.objects.create(
                name='強電系統 (變壓站/配電盤)',
                description='掌握強電系統設計、變壓站與配電盤安裝技術。',
                node_type='CORE', character_class=me,
                exp_reward=100, position_x=MX + 150, position_y=200,
            )
            me_1_2.parent_skills.add(novice_1, novice_2)

            me_1_key = SkillNode.objects.create(
                name='BIM 基礎操作',
                description='【關鍵課程】學習 BIM 軟體基礎操作，解鎖「平板 (BIM Viewer)」工具。',
                node_type='CORE', character_class=me,
                exp_reward=150, position_x=MX + 300, position_y=200,
            )
            me_1_key.parent_skills.add(me_1_1, me_1_2)

            me_2_1 = SkillNode.objects.create(
                name='中央空調系統負載計算',
                description='學習中央空調系統設計與負載計算技術。',
                node_type='CORE', character_class=me,
                exp_reward=150, position_x=MX, position_y=400,
            )
            me_2_1.parent_skills.add(me_1_key)

            me_2_2 = SkillNode.objects.create(
                name='弱電與智慧建築系統',
                description='掌握弱電系統與智慧建築整合技術。',
                node_type='CORE', character_class=me,
                exp_reward=150, position_x=MX + 150, position_y=400,
            )
            me_2_2.parent_skills.add(me_1_key)

            me_2_key = SkillNode.objects.create(
                name='熱影像檢測技術',
                description='【關鍵課程】學習熱影像檢測技術，解鎖「熱顯像儀」工具。',
                node_type='ADVANCED', character_class=me,
                exp_reward=200, position_x=MX + 300, position_y=400,
            )
            me_2_key.parent_skills.add(me_2_1, me_2_2)

            me_3_1 = SkillNode.objects.create(
                name='機電系統測試與運轉 (T&C)',
                description='學習機電系統測試與試運轉程序。',
                node_type='ADVANCED', character_class=me,
                exp_reward=250, position_x=MX, position_y=600,
            )
            me_3_1.parent_skills.add(me_2_key)

            me_3_2 = SkillNode.objects.create(
                name='綠建築與節能規劃',
                description='掌握綠建築設計與節能系統規劃技術。',
                node_type='ADVANCED', character_class=me,
                exp_reward=250, position_x=MX + 150, position_y=600,
            )
            me_3_2.parent_skills.add(me_2_key)

            me_3_key = SkillNode.objects.create(
                name='混合實境 (MR) 應用',
                description='【關鍵課程】學習 MR 技術應用，解鎖「MR 智慧眼鏡」工具。',
                node_type='ADVANCED', character_class=me,
                exp_reward=300, position_x=MX + 300, position_y=600,
            )
            me_3_key.parent_skills.add(me_3_1, me_3_2)

            # ═══════════════════════════════════════
            # 職安僧侶 (Safety Monk)
            # x 偏移 = 1000
            # ═══════════════════════════════════════
            self.stdout.write('\n🛡️  創建職安僧侶技能樹...')
            SX = 1000  # X offset

            safety_1_1 = SkillNode.objects.create(
                name='施工架與支撐作業安全',
                description='學習施工架組立、支撐系統安全檢查技術。',
                node_type='CORE', character_class=safety,
                exp_reward=100, position_x=SX, position_y=200,
            )
            safety_1_1.parent_skills.add(novice_3)

            safety_1_2 = SkillNode.objects.create(
                name='局限空間危害預防',
                description='掌握局限空間作業危害辨識與預防措施。',
                node_type='CORE', character_class=safety,
                exp_reward=100, position_x=SX + 150, position_y=200,
            )
            safety_1_2.parent_skills.add(novice_3)

            safety_1_key = SkillNode.objects.create(
                name='環境監測儀器實務',
                description='【關鍵課程】學習環境監測儀器操作，解鎖「四用氣體偵測器」工具。',
                node_type='CORE', character_class=safety,
                exp_reward=150, position_x=SX + 300, position_y=200,
            )
            safety_1_key.parent_skills.add(safety_1_1, safety_1_2)

            safety_2_1 = SkillNode.objects.create(
                name='重型機具吊掛作業安全',
                description='學習重型機具操作與吊掛作業安全管理。',
                node_type='CORE', character_class=safety,
                exp_reward=150, position_x=SX, position_y=400,
            )
            safety_2_1.parent_skills.add(safety_1_key)

            safety_2_2 = SkillNode.objects.create(
                name='噪音與振動量測',
                description='掌握工地噪音與振動量測技術與法規標準。',
                node_type='CORE', character_class=safety,
                exp_reward=150, position_x=SX + 150, position_y=400,
            )
            safety_2_2.parent_skills.add(safety_1_key)

            safety_2_key = SkillNode.objects.create(
                name='智慧監控系統',
                description='【關鍵課程】學習智慧監控系統應用，解鎖「噪音計/振動計」工具。',
                node_type='ADVANCED', character_class=safety,
                exp_reward=200, position_x=SX + 300, position_y=400,
            )
            safety_2_key.parent_skills.add(safety_2_1, safety_2_2)

            safety_3_1 = SkillNode.objects.create(
                name='重大職災調查與分析',
                description='學習職業災害調查技術與事故原因分析方法。',
                node_type='ADVANCED', character_class=safety,
                exp_reward=250, position_x=SX, position_y=600,
            )
            safety_3_1.parent_skills.add(safety_2_key)

            safety_3_2 = SkillNode.objects.create(
                name='ISO 45001 管理系統',
                description='掌握 ISO 45001 職業安全衛生管理系統建置與稽核。',
                node_type='ADVANCED', character_class=safety,
                exp_reward=250, position_x=SX + 150, position_y=600,
            )
            safety_3_2.parent_skills.add(safety_2_key)

            safety_3_key = SkillNode.objects.create(
                name='體感模擬訓練',
                description='【關鍵課程】學習 VR 體感模擬訓練技術，解鎖「VR 體感設備」工具。',
                node_type='ADVANCED', character_class=safety,
                exp_reward=300, position_x=SX + 300, position_y=600,
            )
            safety_3_key.parent_skills.add(safety_3_1, safety_3_2)

            # ═══════════════════════════════════════
            # 統計
            # ═══════════════════════════════════════
            total     = SkillNode.objects.count()
            roots     = SkillNode.objects.filter(node_type='ROOT').count()
            cores     = SkillNode.objects.filter(node_type='CORE').count()
            advanced  = SkillNode.objects.filter(node_type='ADVANCED').count()

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS('✅ 技能樹初始化完成！'))
            self.stdout.write(f'   📊 總數：{total}')
            self.stdout.write(f'   🌱 ROOT：{roots}')
            self.stdout.write(f'   🌳 CORE：{cores}')
            self.stdout.write(f'   🍃 ADVANCED：{advanced}')
            self.stdout.write(f'   ⚔️  土木戰士：{SkillNode.objects.filter(character_class=civil).count()}')
            self.stdout.write(f'   🔮 機電法師：{SkillNode.objects.filter(character_class=me).count()}')
            self.stdout.write(f'   🛡️  職安僧侶：{SkillNode.objects.filter(character_class=safety).count()}')
            self.stdout.write(self.style.SUCCESS('=' * 60))
