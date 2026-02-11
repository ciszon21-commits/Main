from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json
import math


class CharacterClass(models.Model):
    """職業類別：土木戰士、機電法師、職安僧侶"""
    
    CLASS_CHOICES = [
        ('CIVIL', '土木戰士 (Civil Warrior)'),
        ('ME', '機電法師 (M&E Mage)'),
        ('SAFETY', '職安僧侶 (Safety Monk)'),
    ]
    
    code = models.CharField('職業代碼', max_length=10, choices=CLASS_CHOICES, unique=True)
    name = models.CharField('職業名稱', max_length=50)
    description = models.TextField('職業描述')
    base_hp = models.IntegerField('基礎HP', default=3)
    base_mp = models.IntegerField('基礎MP', default=100)
    icon = models.ImageField('職業圖示', upload_to='rpg/class_icons/', null=True, blank=True)
    
    class Meta:
        verbose_name = '職業'
        verbose_name_plural = '職業列表'
        
    def __str__(self):
        return self.name


# ==================== Team System Models ====================

class Team(models.Model):
    name = models.CharField(max_length=200, verbose_name='隊伍名稱')
    description = models.TextField(blank=True, verbose_name='隊伍說明')
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='led_teams', verbose_name='隊長')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='created_teams', verbose_name='建立者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        managed = False
        db_table = 'TeamKnowledgeHub_knowledgeteam'
        verbose_name = '隊伍'
        verbose_name_plural = '隊伍列表'

    def __str__(self):
        return self.name
    
    def get_member_count(self):
        """獲取隊伍成員數量"""
        return self.current_members.count()
    
    def is_leader(self, user):
        """檢查使用者是否為隊長"""
        return self.leader == user

class TeamMembership(models.Model):
    ROLE_CHOICES = [
        ('MEMBER', '成員'),
        ('LEADER', '隊長'),
        ('VICE_LEADER', '副隊長'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    role = models.CharField(max_length=20)
    joined_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'TeamKnowledgeHub_knowledgeteammember'
        unique_together = (('team', 'user'),)
        verbose_name = '隊伍成員'
        verbose_name_plural = '隊伍成員列表'
        
    def __str__(self):
        return f"{self.user.username} - {self.team.name}"


class UserProfile(models.Model):
    """使用者檔案 - 擴充 Django User"""
    
    ROLE_CHOICES = [
        ('ADVENTURER', '冒險者'),
        ('OFFICER', '公會幹部'),
        ('MANAGER', '公會會長'),
        ('ADMIN', '創世神'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rpg_profile')
    employee_id = models.CharField('員工編號', max_length=20, unique=True)
    character_class = models.ForeignKey(CharacterClass, on_delete=models.PROTECT, verbose_name='職業')
    role = models.CharField('角色權限', max_length=20, choices=ROLE_CHOICES, default='ADVENTURER')
    
    # 角色屬性
    level = models.IntegerField('等級', default=1, validators=[MinValueValidator(1)])
    experience = models.IntegerField('經驗值', default=0, validators=[MinValueValidator(0)])
    hp = models.IntegerField('生命值', default=3)
    mp = models.IntegerField('技能值', default=100)
    
    RANK_CHOICES = [
        ('INTERN', '實習生'),
        ('ASSISTANT', '助理工程師'),
        ('ENGINEER', '工程師'),
    ]
    rank = models.CharField('職銜', max_length=20, choices=RANK_CHOICES, default='INTERN')
    

    
    # 裝備欄位
    equipped_helmet = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='equipped_as_helmet', verbose_name='裝備頭盔')
    equipped_armor = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='equipped_as_armor', verbose_name='裝備盔甲')
    equipped_boots = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='equipped_as_boots', verbose_name='裝備靴子')
    equipped_tool_1 = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='equipped_as_tool_1', verbose_name='工具欄1')
    equipped_tool_2 = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='equipped_as_tool_2', verbose_name='工具欄2')
    equipped_tool_3 = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='equipped_as_tool_3', verbose_name='工具欄3')
    equipped_tool_4 = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='equipped_as_tool_4', verbose_name='工具欄4')
    equipped_tool_5 = models.ForeignKey('UserEquipment', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='equipped_as_tool_5', verbose_name='工具欄5')
    
    # 隊伍歸屬
    current_team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='current_members', verbose_name='當前隊伍', db_constraint=False)
    
    # 強化券
    enhancement_tickets = models.IntegerField('強化券數量', default=0, validators=[MinValueValidator(0)])
    
    # 其他資訊
    avatar_image = models.ImageField('角色頭像', upload_to='rpg/avatars/', null=True, blank=True)
    avatar_index = models.IntegerField('預設頭像索引', default=0, help_text='0表示使用上傳頭像或隨機，1-20表示選擇的預設頭像')
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '使用者檔案'
        verbose_name_plural = '使用者檔案'
        
    def __str__(self):
        return f"{self.user.username} - {self.character_class.name} Lv.{self.level}"
    
    def get_total_hp(self):
        """計算總 HP（基礎隨等級成長 + 裝備加成）
        公式：50 + floor((Lv - 1) * 0.5)
        """
        # 基礎 HP
        base_hp = 50 + math.floor((self.level - 1) * 0.5)
        
        # 裝備加成
        equipment_bonus = 0
        for slot in [self.equipped_helmet, self.equipped_armor, self.equipped_boots,
                     self.equipped_tool_1, self.equipped_tool_2, self.equipped_tool_3,
                     self.equipped_tool_4, self.equipped_tool_5]:
            if slot:
                equipment_bonus += slot.get_total_hp_bonus()
        
        return base_hp + equipment_bonus

    def get_total_mp(self):
        """計算總 MP（基礎隨等級成長 + 裝備加成）
        公式：100 + (Lv - 1) * 2
        """
        # 基礎 MP
        base_mp = 100 + (self.level - 1) * 2
        
        # 裝備加成
        equipment_bonus = 0
        for slot in [self.equipped_helmet, self.equipped_armor, self.equipped_boots,
                     self.equipped_tool_1, self.equipped_tool_2, self.equipped_tool_3,
                     self.equipped_tool_4, self.equipped_tool_5]:
            if slot:
                equipment_bonus += slot.get_total_mp_bonus()
        
        return base_mp + equipment_bonus

    def update_stats(self):
        """更新並儲存最新的 HP 和 MP 數值"""
        self.hp = self.get_total_hp()
        self.mp = self.get_total_mp()
        self.save(update_fields=['hp', 'mp'])
    
    def experience_to_next_level(self):
        """計算升級所需經驗值"""
        return self.level * 100  # 簡單公式：等級 * 100
    
    def get_avatar_url(self):
        """獲取頭像 URL，優先級: 上傳圖片 > 指定預設頭像 > 隨機預設頭像"""
        if self.avatar_image:
            return self.avatar_image.url
        elif self.avatar_index > 0:
            return f'/static/EngineerRPG/img/avatars/default_avatar_{self.avatar_index}.png'
        else:
            # 根據用戶 ID 選擇固定的預設頭像（確保同一用戶總是看到相同的頭像）
            # 共有 20 個預設頭像 (4人類 + 4矮人 + 4精靈 + 4獸人 + 4魔族)
            avatar_index = (self.user.id % 20) + 1
            return f'/static/EngineerRPG/img/avatars/default_avatar_{avatar_index}.png'



class SkillNode(models.Model):
    """技能節點 - 技能樹系統"""
    
    NODE_TYPE_CHOICES = [
        ('ROOT', '根部（共同必修）'),
        ('CORE', '主幹（職業核心）'),
        ('ADVANCED', '枝葉（進階選修）'),
    ]
    
    name = models.CharField('技能名稱', max_length=100)
    description = models.TextField('技能描述')
    node_type = models.CharField('節點類型', max_length=20, choices=NODE_TYPE_CHOICES)
    character_class = models.ForeignKey(CharacterClass, on_delete=models.CASCADE, 
                                       verbose_name='所屬職業', null=True, blank=True,
                                       help_text='ROOT 類型可為空，表示所有職業共用')
    
    # 學習限制
    min_level = models.IntegerField('最低等級需求', default=1, validators=[MinValueValidator(1)],
                                   help_text='學習此技能所需的最低角色等級')
    
    # 技能樹結構
    parent_skills = models.ManyToManyField('self', symmetrical=False, blank=True,
                                          related_name='child_skills', verbose_name='前置技能')
    
    # 視覺化
    icon_locked = models.ImageField('未解鎖圖示', upload_to='rpg/skill_icons/', null=True, blank=True)
    icon_unlocked = models.ImageField('已解鎖圖示', upload_to='rpg/skill_icons/', null=True, blank=True)
    position_x = models.IntegerField('X座標', default=0, help_text='技能樹視覺化位置')
    position_y = models.IntegerField('Y座標', default=0, help_text='技能樹視覺化位置')
    
    # 獎勵
    exp_reward = models.IntegerField('完成獎勵經驗值', default=50)
    
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '技能節點'
        verbose_name_plural = '技能節點'
        
    def __str__(self):
        return f"{self.name} ({self.get_node_type_display()})"


class Course(models.Model):
    """課程內容"""
    
    CONTENT_TYPE_CHOICES = [
        ('PDF', 'PDF文件'),
        ('LINK', '外部連結'),
    ]
    
    title = models.CharField('課程標題', max_length=200)
    description = models.TextField('課程描述')
    content_type = models.CharField('內容類型', max_length=10, choices=CONTENT_TYPE_CHOICES)
    content_url = models.URLField('內容網址', max_length=500)
    content_file = models.FileField('內容檔案', upload_to='rpg/courses/', null=True, blank=True)
    
    # 關聯技能
    skill_nodes = models.ManyToManyField(SkillNode, related_name='courses', verbose_name='關聯技能')
    
    duration_minutes = models.IntegerField('課程時長（分鐘）', default=30)
    
    # 考試設定
    questions = models.ManyToManyField('Question', blank=True, verbose_name='考試題目', related_name='courses')
    passing_score = models.IntegerField('及格分數', default=80)
    exam_time_limit = models.IntegerField('考試時限（分鐘）', default=20)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '課程'
        verbose_name_plural = '課程列表'
        
    def __str__(self):
        return self.title


class UserSkill(models.Model):
    """使用者技能進度"""
    
    STATUS_CHOICES = [
        ('LOCKED', '未解鎖'),
        ('AVAILABLE', '可學習'),
        ('IN_PROGRESS', '學習中'),
        ('COMPLETED', '已完成'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    skill_node = models.ForeignKey(SkillNode, on_delete=models.CASCADE)
    status = models.CharField('學習狀態', max_length=20, choices=STATUS_CHOICES, default='LOCKED')
    
    progress = models.IntegerField('學習進度(%)', default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    started_at = models.DateTimeField('開始時間', null=True, blank=True)
    completed_at = models.DateTimeField('完成時間', null=True, blank=True)
    
    class Meta:
        verbose_name = '使用者技能'
        verbose_name_plural = '使用者技能'
        unique_together = ['user_profile', 'skill_node']
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.skill_node.name} ({self.get_status_display()})"


class UserCourseProgress(models.Model):
    """使用者課程進度"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_progress')
    
    is_completed = models.BooleanField('已完成', default=False)
    score = models.IntegerField('最高分數', default=0)
    completed_at = models.DateTimeField('完成時間', null=True, blank=True)
    
    class Meta:
        verbose_name = '使用者課程進度'
        verbose_name_plural = '使用者課程進度'
        unique_together = ['user_profile', 'course']
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.course.title}"


# ==================== 裝備系統 ====================

class Equipment(models.Model):
    """裝備系統 - 頭盔、盔甲、靴子、工具"""
    
    EQUIPMENT_TYPE_CHOICES = [
        ('HELMET', '頭盔 (Helmet)'),
        ('ARMOR', '盔甲 (Armor)'),
        ('BOOTS', '靴子 (Boots)'),
        ('TOOL', '工具 (Tool)'),
    ]
    
    RARITY_CHOICES = [
        ('COMMON', '普通 (Common)'),
        ('RARE', '稀有 (Rare)'),
        ('EPIC', '史詩 (Epic)'),
        ('LEGENDARY', '傳說 (Legendary)'),
    ]
    
    name = models.CharField('裝備名稱', max_length=100)
    description = models.TextField('裝備描述')
    equipment_type = models.CharField('裝備類型', max_length=20, choices=EQUIPMENT_TYPE_CHOICES)
    rarity = models.CharField('稀有度', max_length=20, choices=RARITY_CHOICES, default='COMMON')
    tier = models.IntegerField('階級', default=1, choices=[(1, 'Tier 1'), (2, 'Tier 2'), (3, 'Tier 3')])
    
    # 屬性加成
    hp_bonus = models.IntegerField('HP加成', default=0)
    mp_bonus = models.IntegerField('MP加成', default=0)
    damage_reduction = models.IntegerField('減傷值 (DR)', default=0, help_text='正值表示減傷，例如 2 表示減傷 2 點')
    
    # 強化規則 (JSON)
    # 格式範例: {"0": {"hp": 10, "mp": 0}, "3": {"hp": 15, "mp": 0}, ...}
    enhancement_rules = models.JSONField('強化規則', default=dict, blank=True, help_text='定義各強化等級的詳細數值')
    
    # 技能效果（工具類裝備）
    skill_effect = models.CharField('技能效果', max_length=50, blank=True, null=True)
    skill_description = models.TextField('技能描述', blank=True, null=True)
    mp_cost = models.IntegerField('MP消耗', default=0)
    
    # +9 特殊能力
    special_ability_name = models.CharField('+9 特殊能力名稱', max_length=50, blank=True, null=True)
    special_ability_description = models.TextField('+9 特殊能力描述', blank=True, null=True)
    
    # 解鎖條件
    required_skill = models.ForeignKey('SkillNode', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='需求技能')
    required_level = models.IntegerField('需求等級', default=1)
    
    # 強化
    max_enhancement = models.IntegerField('最大強化等級', default=9)
    
    # 視覺
    icon = models.ImageField('裝備圖示', upload_to='rpg/equipment_icons/', null=True, blank=True)
    
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '裝備'
        verbose_name_plural = '裝備列表'
        
    def __str__(self):
        return f"{self.name} (T{self.tier} {self.get_equipment_type_display()})"


class UserEquipment(models.Model):
    """使用者擁有的裝備"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='owned_equipment')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    
    enhancement_level = models.IntegerField('強化等級', default=0, validators=[MinValueValidator(0)])
    is_equipped = models.BooleanField('是否裝備中', default=False)
    obtained_at = models.DateTimeField('獲得時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '使用者裝備'
        verbose_name_plural = '使用者裝備'
        unique_together = [['user_profile', 'equipment']]
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.equipment.name} (+{self.enhancement_level})"
    
    def _get_stat_from_rules(self, stat_name, default_value):
        """從強化規則中獲取數值，如果沒有則使用預設公式"""
        rules = self.equipment.enhancement_rules
        if not rules:
            return default_value
            
        level_str = str(self.enhancement_level)
        if level_str in rules and stat_name in rules[level_str]:
            return rules[level_str][stat_name]
            
        # 搜尋 <= enhancement_level 的最大 key
        valid_keys = [int(k) for k in rules.keys() if k.isdigit() and int(k) <= self.enhancement_level]
        if valid_keys:
            best_key = str(max(valid_keys))
            return rules[best_key].get(stat_name, 0)
            
        return default_value

    def get_total_hp_bonus(self):
        """計算總HP加成（含強化）"""
        if self.equipment.enhancement_rules:
            return self._get_stat_from_rules('hp', 0)
        return self.equipment.hp_bonus + (self.enhancement_level * 1)
    
    def get_total_mp_bonus(self):
        """計算總MP加成（含強化）"""
        if self.equipment.enhancement_rules:
            return self._get_stat_from_rules('mp', 0)
        return self.equipment.mp_bonus + (self.enhancement_level * 5)

    def get_damage_reduction(self):
        """計算減傷值 (正值為減傷)"""
        if self.equipment.enhancement_rules:
            # 假設規則裡的 dr 是正值 (e.g. 1, 2, 4)
            return self._get_stat_from_rules('dr', 0)
        return self.equipment.damage_reduction


# ==================== 道具系統 ====================

class Item(models.Model):
    """道具系統"""
    
    ITEM_TYPE_CHOICES = [
        ('BASIC', '基礎道具'),
        ('ADVANCED', '進階道具'),
        ('RARE', '稀有道具'),
    ]
    
    EFFECT_TYPE_CHOICES = [
        ('HINT', '提示 (Show Hint)'),
        ('HEAL', '回復 HP (Heal HP)'),
        ('REMOVE_OPTION', '刪除選項 (Remove Option)'),
        ('SHIELD', '抵擋傷害 (Shield)'),
        ('TIME_EXTEND', '延長時間 (Extend Time)'),
        ('DISTRIBUTION', '機率分佈 (Show Distribution)'),
        ('SKIP', '跳題 (Skip Question)'),
        ('COMBO_PROTECT', '連勝保護 (Combo Protect)'),
    ]
    
    RARITY_CHOICES = [
        ('COMMON', '普通 (Common)'),
        ('RARE', '稀有 (Rare)'),
        ('EPIC', '史詩 (Epic)'),
        ('LEGENDARY', '傳說 (Legendary)'),
    ]
    
    name = models.CharField('道具名稱', max_length=100)
    description = models.TextField('道具描述')
    item_type = models.CharField('道具類型', max_length=20, choices=ITEM_TYPE_CHOICES, default='BASIC')
    rarity = models.CharField('稀有度', max_length=20, choices=RARITY_CHOICES, default='COMMON')
    
    # 效果設定
    effect_type = models.CharField('效果類型', max_length=20, choices=EFFECT_TYPE_CHOICES)
    effect_value = models.IntegerField('效果數值', default=0, help_text='例如：回復10% HP則填10，延長30秒則填30')
    
    # 視覺
    icon = models.ImageField('道具圖示', upload_to='rpg/item_icons/', null=True, blank=True)
    
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '道具'
        verbose_name_plural = '道具列表'
        
    def __str__(self):
        return self.name


class UserItem(models.Model):
    """使用者擁有的道具"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    
    quantity = models.IntegerField('數量', default=1, validators=[MinValueValidator(0)])
    obtained_at = models.DateTimeField('獲得時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '使用者道具'
        verbose_name_plural = '使用者道具'
        unique_together = [['user_profile', 'item']]
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.item.name} x{self.quantity}"


class QuestionCategory(models.Model):
    """題目分類（用於地下城與題庫分類）"""
    name = models.CharField('分類名稱', max_length=50, unique=True)
    description = models.TextField('分類描述', blank=True)
    icon = models.ImageField('分類圖示', upload_to='rpg/categories/', null=True, blank=True)
    
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '題目分類'
        verbose_name_plural = '題目分類'
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Question(models.Model):
    """題庫"""
    
    QUESTION_TYPE_CHOICES = [
        ('SINGLE', '單選題'),
        ('MULTIPLE', '多選題'),
        ('TRUEFALSE', '是非題'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('S', 'S級（最難）'),
        ('A', 'A級（困難）'),
        ('B', 'B級（中等）'),
        ('C', 'C級（簡單）'),
    ]
    
    content = models.TextField('題目內容')
    question_type = models.CharField('題目類型', max_length=20, choices=QUESTION_TYPE_CHOICES)
    
    # 選項與答案（JSON 格式）
    options = models.JSONField('選項', default=dict, 
                              help_text='格式: {"A": "選項1", "B": "選項2", ...}')
    correct_answer = models.JSONField('正確答案',
                                     help_text='單選: "A", 多選: ["A", "B"], 是非: "T" or "F"')
    explanation = models.TextField('詳解', blank=True)
    
    # 分類
    difficulty = models.CharField('難度', max_length=1, choices=DIFFICULTY_CHOICES, default='B')
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, 
                                null=True, blank=True, verbose_name='題目分類',
                                related_name='questions')
    tags = models.CharField('標籤', max_length=200, blank=True, 
                           help_text='多個標籤用逗號分隔，例如：鋼筋,法規,職安')
    
    # 關聯技能
    related_skills = models.ManyToManyField(SkillNode, related_name='questions', 
                                           verbose_name='關聯技能', blank=True)
    
    # 圖片
    image = models.ImageField('題目圖片', upload_to='rpg/questions/', null=True, blank=True)
    
    is_active = models.BooleanField('啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '題目'
        verbose_name_plural = '題庫'
        
    def __str__(self):
        return f"[{self.get_difficulty_display()}] {self.content[:50]}"


class Trial(models.Model):
    """試煉（副本）"""
    
    TRIAL_TYPE_CHOICES = [
        ('DAILY', '每日副本'),
        ('DUNGEON', '地下城'),
        ('PROMOTION', '升階試煉'),
        ('SPECIAL', '特殊活動'),
    ]
    
    title = models.CharField('試煉標題', max_length=200)
    description = models.TextField('試煉描述')
    trial_type = models.CharField('試煉類型', max_length=20, choices=TRIAL_TYPE_CHOICES)
    
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='所屬分類',
                                related_name='dungeons',
                                help_text='僅地下城類型需要設定此欄位')
    
    # 題目設定
    questions = models.ManyToManyField(Question, related_name='trials', verbose_name='題目集合')
    question_count = models.IntegerField('題目數量', default=10, 
                                        help_text='從題目集合中隨機抽取的數量')
    time_limit_minutes = models.IntegerField('時間限制（分鐘）', default=30)
    
    # 條件
    required_level = models.IntegerField('需求等級', default=1)
    required_skills = models.ManyToManyField(SkillNode, related_name='required_for_trials',
                                            verbose_name='需求技能', blank=True)
    
    # 獎勵
    exp_reward = models.IntegerField('經驗值獎勵', default=100)
    equipment_reward = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='trial_rewards', verbose_name='裝備獎勵')
    item_reward = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='trial_item_rewards', verbose_name='道具獎勵')
    
    # 每日副本設定
    is_daily = models.BooleanField('每日副本', default=False)
    refresh_date = models.DateField('刷新日期', null=True, blank=True)
    
    is_active = models.BooleanField('啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '試煉'
        verbose_name_plural = '試煉列表'
        
    def __str__(self):
        return f"{self.title} ({self.get_trial_type_display()})"


class TrialRecord(models.Model):
    """試煉記錄"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='trial_records')
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    daily_task = models.ForeignKey('DailyTrialTask', on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name='每日任務',
                                   related_name='records')
    
    # 成績
    score = models.IntegerField('分數')
    total_questions = models.IntegerField('總題數')
    correct_answers = models.IntegerField('答對題數')
    time_spent_seconds = models.IntegerField('花費時間（秒）')
    
    # 答題記錄（JSON）
    answer_details = models.JSONField('答題詳情', default=dict,
                                     help_text='記錄每題的答案與正確性')
    
    # 獎勵
    exp_gained = models.IntegerField('獲得經驗值', default=0)
    equipment_gained = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name='獲得裝備')
    item_gained = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name='獲得道具')
    
    is_passed = models.BooleanField('是否通過', default=False)
    completed_at = models.DateTimeField('完成時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '試煉記錄'
        verbose_name_plural = '試煉記錄'
        ordering = ['-completed_at']
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.trial.title} ({self.score}分)"


class PromotionRequest(models.Model):
    """晉升申請"""
    
    STATUS_CHOICES = [
        ('PENDING', '待審核'),
        ('APPROVED', '已通過'),
        ('REJECTED', '已拒絕'),
    ]
    
    applicant = models.ForeignKey(UserProfile, on_delete=models.CASCADE, 
                                 related_name='promotion_requests', verbose_name='申請人')
    current_level = models.IntegerField('當前等級')
    target_level = models.IntegerField('目標等級')
    
    # 試煉
    trial = models.ForeignKey(Trial, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='升階試煉')
    trial_record = models.ForeignKey(TrialRecord, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='試煉記錄')
    
    # 審核
    status = models.CharField('審核狀態', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='reviewed_promotions', verbose_name='審核人')
    review_comment = models.TextField('審核備註', blank=True)
    
    applied_at = models.DateTimeField('申請時間', auto_now_add=True)
    reviewed_at = models.DateTimeField('審核時間', null=True, blank=True)
    
    class Meta:
        verbose_name = '晉升申請'
        verbose_name_plural = '晉升申請'
        ordering = ['-applied_at']
        
    def __str__(self):
        return f"{self.applicant.user.username} - Lv.{self.current_level}→{self.target_level} ({self.get_status_display()})"


class EnhancementScroll(models.Model):
    """強化卷軸"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, 
                                    related_name='enhancement_scrolls', verbose_name='擁有者')
    quantity = models.IntegerField('數量', default=0, validators=[MinValueValidator(0)])
    
    obtained_at = models.DateTimeField('獲得時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '強化卷軸'
        verbose_name_plural = '強化卷軸'
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.quantity} 個卷軸"


class Achievement(models.Model):
    """成就系統"""
    
    ACHIEVEMENT_TYPE_CHOICES = [
        ('LEVEL', '等級成就'),
        ('SKILL', '技能成就'),
        ('TRIAL', '試煉成就'),
        ('EQUIPMENT', '裝備成就'),
        ('SPECIAL', '特殊成就'),
    ]
    
    name = models.CharField('成就名稱', max_length=100)
    description = models.TextField('成就描述')
    achievement_type = models.CharField('成就類型', max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES)
    
    # 條件（JSON）
    condition = models.JSONField('達成條件', default=dict,
                                help_text='例如：{"level": 10} 或 {"trials_completed": 50}')
    
    # 獎勵
    exp_reward = models.IntegerField('經驗值獎勵', default=0)
    scroll_reward = models.IntegerField('卷軸獎勵', default=0)
    
    icon = models.ImageField('成就圖示', upload_to='rpg/achievements/', null=True, blank=True)
    
    class Meta:
        verbose_name = '成就'
        verbose_name_plural = '成就列表'
        
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """使用者成就"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    
    unlocked_at = models.DateTimeField('解鎖時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '使用者成就'
        verbose_name_plural = '使用者成就'
        unique_together = ['user_profile', 'achievement']
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.achievement.name}"


class DailyTrialTask(models.Model):
    """每日試煉任務"""
    
    date = models.DateField('日期', db_index=True)
    task_number = models.IntegerField('任務編號', 
                                     choices=[(1, '任務一'), (2, '任務二'), (3, '任務三')])
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, verbose_name='試煉')
    questions = models.ManyToManyField(Question, verbose_name='題目')
    is_active = models.BooleanField('啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '每日試煉任務'
        verbose_name_plural = '每日試煉任務'
        unique_together = ['date', 'task_number']
        ordering = ['date', 'task_number']
        
    def __str__(self):
        return f"{self.date} - 任務{self.task_number}: {self.trial.title}"


class DailyTrialProgress(models.Model):
    """每日試煉進度（追蹤每個任務的 HP/MP）"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                    related_name='daily_trial_progress',
                                    verbose_name='使用者')
    daily_task = models.ForeignKey(DailyTrialTask, on_delete=models.CASCADE,
                                   related_name='user_progress',
                                   verbose_name='每日任務')
    
    # HP/MP 追蹤
    current_hp = models.IntegerField('當前 HP')
    current_mp = models.IntegerField('當前 MP')
    initial_hp = models.IntegerField('初始 HP')
    initial_mp = models.IntegerField('初始 MP')
    
    # 狀態
    is_completed = models.BooleanField('已完成', default=False)
    is_passed = models.BooleanField('通過', default=False)
    
    # 時間記錄
    started_at = models.DateTimeField('開始時間', null=True, blank=True)
    completed_at = models.DateTimeField('完成時間', null=True, blank=True)
    
    # 答題記錄（JSON）
    answers = models.JSONField('答題記錄', default=dict, blank=True)
    
    # 當前題目索引（用於狀態保持）
    current_question_index = models.IntegerField('當前題目索引', default=0)
    
    class Meta:
        verbose_name = '每日試煉進度'
        verbose_name_plural = '每日試煉進度'
        unique_together = ['user_profile', 'daily_task']
        
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.daily_task}"


class GuildPost(models.Model):
    """公會交流區貼文"""
    CATEGORY_CHOICES = [
        ('GENERAL', '綜合討論'),
        ('STRATEGY', '攻略心得'),
        ('QA', '問題請教'),
        ('ANNOUNCEMENT', '公會公告'),  # 僅限管理員發布
    ]
    
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='guild_posts', verbose_name='發布者')
    title = models.CharField('標題', max_length=200)
    content = models.TextField('內容')  # 支援 CKEditor
    category = models.CharField('分類', max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    
    views = models.IntegerField('瀏覽數', default=0)
    likes = models.ManyToManyField(UserProfile, related_name='liked_posts', blank=True, verbose_name='按讚')
    
    is_pinned = models.BooleanField('置頂', default=False)
    is_locked = models.BooleanField('鎖定', default=False)
    
    created_at = models.DateTimeField('發布時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '公會貼文'
        verbose_name_plural = '公會貼文'
        ordering = ['-is_pinned', '-created_at']
        
    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"


class GuildComment(models.Model):
    """貼文留言"""
    post = models.ForeignKey(GuildPost, on_delete=models.CASCADE, related_name='comments', verbose_name='貼文')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='guild_comments', verbose_name='留言者')
    content = models.TextField('內容')
    
    created_at = models.DateTimeField('留言時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '公會留言'
        verbose_name_plural = '公會留言'
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.author.user.username} 留言於 {self.post.title}"


