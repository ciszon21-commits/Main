from django.core.management.base import BaseCommand
from EngineerRPG.models import Equipment, SkillNode

class Command(BaseCommand):
    help = 'Populates the equipment database with the new 13 items'

    def handle(self, *args, **options):
        self.stdout.write('Starting equipment population...')
        
        # 2.1 頭部裝備 (Head Gear) - MP
        head_gear = [
            {
                "name": "標準工地帽",
                "tier": 1,
                "type": "HELMET",
                "description": "基本的工地防護裝備。",
                "hp_bonus": 0, "mp_bonus": 10, "dr": 0,
                "rules": {
                    "0": {"mp": 10}, "3": {"mp": 15}, "6": {"mp": 20}, "9": {"mp": 30}
                },
                "special_name": "【新手運】",
                "special_desc": "試煉開始隨機獲得 10~30 MP。"
            },
            {
                "name": "透氣型探照盔",
                "tier": 2,
                "type": "HELMET",
                "description": "附帶照明功能的進階頭盔。",
                "hp_bonus": 0, "mp_bonus": 25, "dr": 0,
                "rules": {
                    "0": {"mp": 25}, "3": {"mp": 35}, "6": {"mp": 45}, "9": {"mp": 60}
                },
                "special_name": "【照明優化】",
                "special_desc": "視線不良/困難題，受傷額外 -1。"
            },
            {
                "name": "AR 智慧工安盔",
                "tier": 3,
                "type": "HELMET",
                "description": "結合AR技術的高科技頭盔。",
                "hp_bonus": 0, "mp_bonus": 50, "dr": 0,
                "rules": {
                    "0": {"mp": 50}, "3": {"mp": 60}, "6": {"mp": 75}, "9": {"mp": 100}
                },
                "special_name": "【工頭威嚴】",
                "special_desc": "進場初始 MP 額外 +10% (可突破上限)。"
            }
        ]

        # 2.2 身體裝備 (Chest Gear) - HP & DR
        chest_gear = [
            {
                "name": "反光背心",
                "tier": 1,
                "type": "ARMOR",
                "description": "基本的反光背心，聊勝於無。",
                "hp_bonus": 10, "mp_bonus": 0, "dr": 0,
                "rules": {
                    "0": {"hp": 10, "dr": 0}, "3": {"hp": 15, "dr": 0}, 
                    "6": {"hp": 20, "dr": 0}, "9": {"hp": 30, "dr": 1} # Requirement says DR -1, model help text says positive is reduction
                },
                "special_name": "【舊衣哲學】",
                "special_desc": "終於獲得減傷 -1 的效果。"
            },
            {
                "name": "監工戰術背心",
                "tier": 2,
                "type": "ARMOR",
                "description": "多功能戰術背心，提供不錯的防護。",
                "hp_bonus": 20, "mp_bonus": 0, "dr": 2,
                "rules": {
                    "0": {"hp": 20, "dr": 2}, "3": {"hp": 30, "dr": 2}, 
                    "6": {"hp": 40, "dr": 2}, "9": {"hp": 55, "dr": 3}
                },
                "special_name": "【緊急包紮】",
                "special_desc": "HP < 30% 時，自動回復 15 HP (限一次)。"
            },
            {
                "name": "外骨骼省力套裝",
                "tier": 3,
                "type": "ARMOR",
                "description": "動力外骨骼，大幅減輕負擔。",
                "hp_bonus": 30, "mp_bonus": 0, "dr": 4,
                "rules": {
                    "0": {"hp": 30, "dr": 4}, "3": {"hp": 45, "dr": 4}, 
                    "6": {"hp": 60, "dr": 4}, "9": {"hp": 80, "dr": 5}
                },
                "special_name": "【危機防護】",
                "special_desc": "HP < 20% 時，減傷效果翻倍 (變為 -10)。"
            }
        ]

        # 2.3 腿部裝備 (Leg Gear) - Logic Descriptions (MP Regen logic is handled in code/frontend not pure stats)
        # We will store the descriptions in the 'description' or maybe special ability?
        # The prompt implies these have passive effects. I'll put the effect description in description for now.
        leg_gear = [
            {
                "name": "鋼頭安全鞋",
                "tier": 1,
                "type": "BOOTS",
                "description": "保護腳趾的鋼頭鞋。(基礎步伐: 3連對回5MP)",
                "hp_bonus": 0, "mp_bonus": 0, "dr": 0,
                "rules": {
                    # Rules for logical effects might need a different field or just strictly strictly UI/Code logic
                    # Storing the upgraded effect numericals if needed, or just text
                    "0": {"desc": "3 連對 回 5 MP"},
                    "3": {"desc": "3 連對 回 6 MP"},
                    "6": {"desc": "3 連對 回 7 MP"},
                    "9": {"desc": "2 連對 回 5 MP"}
                },
                "special_name": "【輕量化鋼頭】",
                "special_desc": "觸發門檻降低為連續答對 2 題。"
            },
            {
                "name": "防穿刺工靴",
                "tier": 2,
                "type": "BOOTS",
                "description": "防穿刺底板。(穩健推進: 一般回1 困難回3)",
                "hp_bonus": 0, "mp_bonus": 0, "dr": 0,
                "rules": {
                     "0": {"desc": "一般回 1 困難回 3"},
                     "3": {"desc": "一般回 1 困難回 4"},
                     "6": {"desc": "一般回 1 困難回 5"},
                     "9": {"desc": "一般回 2 困難回 5"}
                },
                "special_name": "【抓地力強化】",
                "special_desc": "一般題回復量提升至 2 MP。"
            },
            {
                "name": "動力樣板護腿",
                "tier": 3,
                "type": "BOOTS",
                "description": "提供額外動力的護腿。(動能回收: 技能後持續3題)",
                "hp_bonus": 0, "mp_bonus": 0, "dr": 0,
                "rules": {
                    "0": {"desc": "技能後 持續 3 題"},
                    "3": {"desc": "技能後 持續 4 題"},
                    "6": {"desc": "技能後 持續 5 題"},
                    "9": {"desc": "持續 5 題"}
                },
                "special_name": "【永動機】",
                "special_desc": "答對題時額外 10% 機率回 10 MP。"
            }
        ]

        # 3. 工具系統 (Tool System)
        tools = [
            {
                "name": "工程查驗 APP",
                "tier": 1,
                "type": "TOOL",
                "description": "標準化稽核工具。",
                "skill_effect": "SHIELD",
                "skill_desc": "傷害護盾 (Shield)", # Mapping to simplified logic
                "mp_cost": 20,
                "rules": {
                    "0": {"shield": 20, "cost": 20},
                    "3": {"shield": 25, "cost": 25},
                    "6": {"shield": 30, "cost": 30},
                    "9": {"shield": 35, "cost": 35}
                },
                "special_name": "【反饋】",
                "special_desc": "若護盾自然耗盡，返還 20 MP。"
            },
            {
                "name": "UAV 監造無人機",
                "tier": 3,
                "type": "TOOL",
                "description": "全域掃描與選項刪去。",
                "skill_effect": "ELIMINATION",
                "skill_desc": "選項刪去 (Elimination)",
                "mp_cost": 30,
                "rules": {
                    "0": {"buff_duration": 0, "cost": 30},
                    "3": {"buff_duration": 3, "cost": 30},
                    "6": {"buff_duration": 3, "cost": 25},
                    "9": {"buff_duration": 5, "cost": 25}
                },
                "special_name": "【廣域訊號】",
                "special_desc": "減傷 Buff 延長至 5 題。"
            },
            {
                "name": "360 環景相機",
                "tier": 3,
                "type": "TOOL",
                "description": "存檔與回溯。",
                "skill_effect": "TIME_REWIND",
                "skill_desc": "存檔與回溯 (Save & Load)",
                "mp_cost": 35,
                "rules": {
                    "0": {"cost": 35},
                    "3": {"cost": 30},
                    "6": {"cost": 25},
                    "9": {"cost": 20}
                },
                "special_name": "【縮時攝影】",
                "special_desc": "若答對(無回溯)，下次使用消耗減半。"
            },
            {
                "name": "VR 虛擬實境眼鏡",
                "tier": 3,
                "type": "TOOL",
                "description": "絕對解答。",
                "skill_effect": "ABSOLUTE_ANSWER",
                "skill_desc": "絕對解答 (Absolute Answer)",
                "mp_cost": 70,
                "rules": {
                    "0": {"cost": 70},
                    "3": {"cost": 60},
                    "6": {"cost": 50},
                    "9": {"cost": 40}
                },
                "special_name": "【沉浸學習】",
                "special_desc": "發動能力時，額外回復 20 HP。"
            }
        ]

        all_items = head_gear + chest_gear + leg_gear + tools
        
        for item_data in all_items:
            obj, created = Equipment.objects.update_or_create(
                name=item_data["name"],
                defaults={
                    "equipment_type": item_data["type"],
                    "tier": item_data.get("tier", 1),
                    "description": item_data["description"],
                    "hp_bonus": item_data.get("hp_bonus", 0),
                    "mp_bonus": item_data.get("mp_bonus", 0),
                    "damage_reduction": item_data.get("dr", 0),
                    "enhancement_rules": item_data.get("rules", {}),
                    "skill_effect": item_data.get("skill_effect"),
                    "skill_description": item_data.get("skill_desc"),
                    "mp_cost": item_data.get("mp_cost", 0),
                    "special_ability_name": item_data.get("special_name"),
                    "special_ability_description": item_data.get("special_desc"),
                    "max_enhancement": 9
                }
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} {obj.name}")

        self.stdout.write(self.style.SUCCESS('Successfully populated equipment data'))
