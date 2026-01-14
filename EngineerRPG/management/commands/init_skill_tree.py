"""
初始化技能樹資料
創建三種職業的技能樹結構和課程
"""

from django.core.management.base import BaseCommand
from EngineerRPG.models import CharacterClass, SkillNode, Course


class Command(BaseCommand):
    help = '初始化技能樹和課程資料'

    def handle(self, *args, **options):
        self.stdout.write('開始初始化技能樹資料...')
        
        # 獲取職業
        try:
            civil = CharacterClass.objects.get(code='CIVIL')
            me = CharacterClass.objects.get(code='ME')
            safety = CharacterClass.objects.get(code='SAFETY')
        except CharacterClass.DoesNotExist:
            self.stdout.write(self.style.ERROR('請先執行 init_rpg_data 創建職業資料'))
            return
        
        # 創建 ROOT 技能（共同必修）
        self.stdout.write('創建共同必修技能...')
        
        root_skills = []
        
        skill_1 = SkillNode.objects.get_or_create(
            name='工地管理基礎',
            defaults={
                'description': '學習工地管理的基本概念，包括工地組織、人員配置、資源管理等基礎知識。',
                'node_type': 'ROOT',
                'character_class': None,
                'exp_reward': 100,
                'position_x': 0,
                'position_y': 0,
            }
        )[0]
        root_skills.append(skill_1)
        
        skill_2 = SkillNode.objects.get_or_create(
            name='安全規範概論',
            defaults={
                'description': '了解工地安全的基本規範，包括職業安全衛生法、安全標準作業程序等。',
                'node_type': 'ROOT',
                'character_class': None,
                'exp_reward': 100,
                'position_x': 1,
                'position_y': 0,
            }
        )[0]
        root_skills.append(skill_2)
        
        skill_3 = SkillNode.objects.get_or_create(
            name='施工圖識讀',
            defaults={
                'description': '學習閱讀和理解各類施工圖說，包括建築圖、結構圖、機電圖等。',
                'node_type': 'ROOT',
                'character_class': None,
                'exp_reward': 100,
                'position_x': 2,
                'position_y': 0,
            }
        )[0]
        root_skills.append(skill_3)
        
        # 創建土木戰士技能
        self.stdout.write('創建土木戰士技能...')
        
        civil_core_1 = SkillNode.objects.get_or_create(
            name='鋼筋工程',
            defaults={
                'description': '學習鋼筋加工、綁紮、查驗等專業技術，確保結構安全。',
                'node_type': 'CORE',
                'character_class': civil,
                'exp_reward': 150,
                'position_x': 0,
                'position_y': 1,
            }
        )[0]
        civil_core_1.parent_skills.add(skill_1, skill_3)
        
        civil_core_2 = SkillNode.objects.get_or_create(
            name='混凝土工程',
            defaults={
                'description': '掌握混凝土配比、澆置、養護等技術，確保混凝土品質。',
                'node_type': 'CORE',
                'character_class': civil,
                'exp_reward': 150,
                'position_x': 1,
                'position_y': 1,
            }
        )[0]
        civil_core_2.parent_skills.add(skill_1, skill_3)
        
        civil_adv_1 = SkillNode.objects.get_or_create(
            name='預力工程',
            defaults={
                'description': '學習預力混凝土的設計、施工與查驗技術。',
                'node_type': 'ADVANCED',
                'character_class': civil,
                'exp_reward': 200,
                'position_x': 0,
                'position_y': 2,
            }
        )[0]
        civil_adv_1.parent_skills.add(civil_core_1, civil_core_2)
        
        civil_adv_2 = SkillNode.objects.get_or_create(
            name='基礎工程',
            defaults={
                'description': '掌握各類基礎工程的施工技術，包括連續壁、排樁等。',
                'node_type': 'ADVANCED',
                'character_class': civil,
                'exp_reward': 200,
                'position_x': 1,
                'position_y': 2,
            }
        )[0]
        civil_adv_2.parent_skills.add(civil_core_1)
        
        # 創建機電法師技能
        self.stdout.write('創建機電法師技能...')
        
        me_core_1 = SkillNode.objects.get_or_create(
            name='電氣系統',
            defaults={
                'description': '學習建築電氣系統的設計、安裝與測試技術。',
                'node_type': 'CORE',
                'character_class': me,
                'exp_reward': 150,
                'position_x': 0,
                'position_y': 1,
            }
        )[0]
        me_core_1.parent_skills.add(skill_1, skill_3)
        
        me_core_2 = SkillNode.objects.get_or_create(
            name='空調系統',
            defaults={
                'description': '掌握空調系統的規劃、施工與調試技術。',
                'node_type': 'CORE',
                'character_class': me,
                'exp_reward': 150,
                'position_x': 1,
                'position_y': 1,
            }
        )[0]
        me_core_2.parent_skills.add(skill_1, skill_3)
        
        me_adv_1 = SkillNode.objects.get_or_create(
            name='智慧建築',
            defaults={
                'description': '學習智慧建築系統整合技術，包括 BAS、安防系統等。',
                'node_type': 'ADVANCED',
                'character_class': me,
                'exp_reward': 200,
                'position_x': 0,
                'position_y': 2,
            }
        )[0]
        me_adv_1.parent_skills.add(me_core_1, me_core_2)
        
        me_adv_2 = SkillNode.objects.get_or_create(
            name='能源管理',
            defaults={
                'description': '掌握建築能源管理系統的規劃與實施技術。',
                'node_type': 'ADVANCED',
                'character_class': me,
                'exp_reward': 200,
                'position_x': 1,
                'position_y': 2,
            }
        )[0]
        me_adv_2.parent_skills.add(me_core_1, me_core_2)
        
        # 創建職安僧侶技能
        self.stdout.write('創建職安僧侶技能...')
        
        safety_core_1 = SkillNode.objects.get_or_create(
            name='職業安全衛生法規',
            defaults={
                'description': '深入學習職安法規，包括法令解釋、罰則與實務應用。',
                'node_type': 'CORE',
                'character_class': safety,
                'exp_reward': 150,
                'position_x': 0,
                'position_y': 1,
            }
        )[0]
        safety_core_1.parent_skills.add(skill_2)
        
        safety_core_2 = SkillNode.objects.get_or_create(
            name='危害辨識與風險評估',
            defaults={
                'description': '學習工地危害辨識技術與風險評估方法。',
                'node_type': 'CORE',
                'character_class': safety,
                'exp_reward': 150,
                'position_x': 1,
                'position_y': 1,
            }
        )[0]
        safety_core_2.parent_skills.add(skill_2)
        
        safety_adv_1 = SkillNode.objects.get_or_create(
            name='職災調查與分析',
            defaults={
                'description': '掌握職業災害調查技術與事故原因分析方法。',
                'node_type': 'ADVANCED',
                'character_class': safety,
                'exp_reward': 200,
                'position_x': 0,
                'position_y': 2,
            }
        )[0]
        safety_adv_1.parent_skills.add(safety_core_1, safety_core_2)
        
        safety_adv_2 = SkillNode.objects.get_or_create(
            name='安全稽核',
            defaults={
                'description': '學習安全管理系統稽核技術與改善方法。',
                'node_type': 'ADVANCED',
                'character_class': safety,
                'exp_reward': 200,
                'position_x': 1,
                'position_y': 2,
            }
        )[0]
        safety_adv_2.parent_skills.add(safety_core_1, safety_core_2)
        
        # 創建示範課程
        self.stdout.write('創建示範課程...')
        
        course_1 = Course.objects.get_or_create(
            title='工地管理實務',
            defaults={
                'description': '介紹工地管理的實務操作，包括進度管理、品質管理等。',
                'content_type': 'VIDEO',
                'content_url': 'https://example.com/course1',
                'duration_minutes': 60,
            }
        )[0]
        course_1.skill_nodes.add(skill_1)
        
        course_2 = Course.objects.get_or_create(
            title='鋼筋工程施工規範',
            defaults={
                'description': '詳細說明鋼筋工程的施工規範與查驗要點。',
                'content_type': 'PDF',
                'content_url': 'https://example.com/course2.pdf',
                'duration_minutes': 45,
            }
        )[0]
        course_2.skill_nodes.add(civil_core_1)
        
        course_3 = Course.objects.get_or_create(
            title='電氣系統設計基礎',
            defaults={
                'description': '電氣系統設計的基本原理與實務應用。',
                'content_type': 'VIDEO',
                'content_url': 'https://example.com/course3',
                'duration_minutes': 90,
            }
        )[0]
        course_3.skill_nodes.add(me_core_1)
        
        course_4 = Course.objects.get_or_create(
            title='職安法規解析',
            defaults={
                'description': '職業安全衛生法規的詳細解析與案例說明。',
                'content_type': 'PPT',
                'content_url': 'https://example.com/course4.pptx',
                'duration_minutes': 120,
            }
        )[0]
        course_4.skill_nodes.add(safety_core_1)
        
        self.stdout.write(self.style.SUCCESS('✅ 技能樹資料初始化完成！'))
        self.stdout.write(f'   - 共同必修技能：{len(root_skills)} 個')
        self.stdout.write(f'   - 土木戰士技能：4 個')
        self.stdout.write(f'   - 機電法師技能：4 個')
        self.stdout.write(f'   - 職安僧侶技能：4 個')
        self.stdout.write(f'   - 示範課程：4 個')
