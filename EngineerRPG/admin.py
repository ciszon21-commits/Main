import os
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.templatetags.static import static


def _equipment_icon_static_url(icon_value):
    """將 media 路徑轉換為 static URL"""
    if not icon_value:
        return ''
    icon_str = str(icon_value)
    if icon_str.startswith('EngineerRPG/img/equipment_icons/'):
        return static(icon_str)
    filename = os.path.basename(icon_str)
    return static(f'EngineerRPG/img/equipment_icons/{filename}')
from .models import (
    CharacterClass, UserProfile, SkillNode, Course, UserSkill,
    Equipment, UserEquipment, Item, UserItem, Question, Trial, TrialRecord,
    PromotionRequest, EnhancementScroll, Achievement, UserAchievement,
    Team, TeamMembership, DailyTrialTask, DailyTrialProgress
)


# 重新註冊 User 模型以支援自動完成
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    自訂 User Admin，保留 Django 預設的密碼管理功能
    """
    # 繼承 BaseUserAdmin 的所有功能，包括密碼欄位
    # 只額外添加搜尋功能
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    # 確保使用 BaseUserAdmin 的 fieldsets（包含密碼）
    # 如果需要自訂，可以覆寫 fieldsets，但必須包含密碼相關欄位

@admin.register(CharacterClass)
class CharacterClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'base_hp', 'base_mp', 'icon_preview']
    list_filter = ['code']
    search_fields = ['name', 'description']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="50" height="50" />', obj.icon.url)
        return '-'
    icon_preview.short_description = '圖示預覽'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'character_class', 'current_team', 'level', 'experience', 'role', 'created_at']
    list_filter = ['character_class', 'role', 'level', 'current_team']
    search_fields = ['user__username', 'employee_id', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user', 'employee_id', 'character_class', 'role')
        }),
        ('角色屬性', {
            'fields': ('level', 'experience', 'hp', 'mp')
        }),
        ('隊伍', {
            'fields': ('current_team',)
        }),
        ('裝備', {
            'fields': ('equipped_helmet', 'equipped_armor', 'equipped_boots', 
                       'equipped_tool_1', 'equipped_tool_2', 'equipped_tool_3', 
                       'equipped_tool_4', 'equipped_tool_5')
        }),
        ('其他', {
            'fields': ('avatar_image', 'created_at', 'updated_at')
        }),
    )


@admin.register(SkillNode)
class SkillNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'node_type', 'character_class', 'exp_reward', 'position_display']
    list_filter = ['node_type', 'character_class']
    search_fields = ['name', 'description']
    filter_horizontal = ['parent_skills']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'description', 'node_type', 'character_class')
        }),
        ('技能樹結構', {
            'fields': ('parent_skills', 'position_x', 'position_y')
        }),
        ('視覺化', {
            'fields': ('icon_locked', 'icon_unlocked')
        }),
        ('獎勵', {
            'fields': ('exp_reward',)
        }),
    )
    
    def position_display(self, obj):
        return f"({obj.position_x}, {obj.position_y})"
    position_display.short_description = '座標'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'duration_minutes', 'created_at']
    list_filter = ['content_type']
    search_fields = ['title', 'description']
    filter_horizontal = ['skill_nodes']
    
    fieldsets = (
        ('課程資訊', {
            'fields': ('title', 'description', 'content_type', 'duration_minutes')
        }),
        ('內容', {
            'fields': ('content_url', 'content_file')
        }),
        ('關聯技能', {
            'fields': ('skill_nodes',)
        }),
    )


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'skill_node', 'status', 'progress', 'completed_at']
    list_filter = ['status', 'skill_node__character_class']
    search_fields = ['user_profile__user__username', 'skill_node__name']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment_type', 'tier', 'rarity', 'hp_bonus', 'mp_bonus', 'required_level', 'icon_preview']
    list_filter = ['equipment_type', 'tier', 'rarity', 'required_level']
    search_fields = ['name', 'description']

    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'description', 'equipment_type', 'rarity', 'tier')
        }),
        ('屬性加成', {
            'fields': ('hp_bonus', 'mp_bonus', 'damage_reduction')
        }),
        ('技能效果', {
            'fields': ('skill_effect', 'skill_description', 'mp_cost')
        }),
        ('+9 特殊能力', {
            'fields': ('special_ability_name', 'special_ability_description')
        }),
        ('解鎖條件', {
            'fields': ('required_skill', 'required_level')
        }),
        ('強化', {
            'fields': ('max_enhancement', 'enhancement_rules')
        }),
        ('視覺', {
            'fields': ('icon',)
        }),
    )

    def icon_preview(self, obj):
        if obj.icon:
            url = _equipment_icon_static_url(obj.icon)
            return format_html('<img src="{}" width="50" height="50" />', url)
        return '-'
    icon_preview.short_description = '圖示'


@admin.register(UserEquipment)
class UserEquipmentAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'equipment', 'enhancement_level', 'is_equipped', 'obtained_at']
    list_filter = ['is_equipped', 'equipment__equipment_type', 'enhancement_level']
    search_fields = ['user_profile__user__username', 'equipment__name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_type', 'rarity', 'effect_type', 'effect_value', 'icon_preview']
    list_filter = ['item_type', 'rarity', 'effect_type']
    search_fields = ['name', 'description']

    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'description', 'item_type', 'rarity')
        }),
        ('效果', {
            'fields': ('effect_type', 'effect_value')
        }),
        ('視覺', {
            'fields': ('icon',)
        }),
    )

    def icon_preview(self, obj):
        if obj.icon:
            url = _equipment_icon_static_url(obj.icon)
            return format_html('<img src="{}" width="50" height="50" />', url)
        return '-'
    icon_preview.short_description = '圖示'


@admin.register(UserItem)
class UserItemAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'item', 'quantity', 'obtained_at']
    list_filter = ['item__item_type', 'item__rarity']
    search_fields = ['user_profile__user__username', 'item__name']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'question_type', 'difficulty', 'tags', 'is_active', 'created_at']
    list_filter = ['question_type', 'difficulty', 'is_active']
    search_fields = ['content', 'tags']
    filter_horizontal = ['related_skills']
    
    fieldsets = (
        ('題目內容', {
            'fields': ('content', 'question_type', 'image')
        }),
        ('選項與答案', {
            'fields': ('options', 'correct_answer', 'explanation')
        }),
        ('分類', {
            'fields': ('difficulty', 'tags', 'related_skills')
        }),
        ('狀態', {
            'fields': ('is_active',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '題目內容'
    
    actions = ['activate_questions', 'deactivate_questions']
    
    def activate_questions(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'已啟用 {queryset.count()} 個題目')
    activate_questions.short_description = '啟用選中的題目'
    
    def deactivate_questions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'已停用 {queryset.count()} 個題目')
    deactivate_questions.short_description = '停用選中的題目'


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ['title', 'trial_type', 'question_count', 'time_limit_minutes', 'required_level', 'is_active']
    list_filter = ['trial_type', 'is_active', 'is_daily']
    search_fields = ['title', 'description']
    filter_horizontal = ['questions', 'required_skills']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'description', 'trial_type')
        }),
        ('題目設定', {
            'fields': ('questions', 'question_count', 'time_limit_minutes')
        }),
        ('條件', {
            'fields': ('required_level', 'required_skills')
        }),
        ('獎勵', {
            'fields': ('exp_reward', 'equipment_reward', 'item_reward')
        }),
        ('每日副本', {
            'fields': ('is_daily', 'refresh_date')
        }),
        ('狀態', {
            'fields': ('is_active',)
        }),
    )


@admin.register(TrialRecord)
class TrialRecordAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'trial', 'score', 'correct_answers', 'total_questions', 'is_passed', 'completed_at']
    list_filter = ['is_passed', 'trial__trial_type', 'completed_at']
    search_fields = ['user_profile__user__username', 'trial__title']
    readonly_fields = ['completed_at']
    
    def has_add_permission(self, request):
        return False  # 記錄只能由系統生成


@admin.register(PromotionRequest)
class PromotionRequestAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'level_change', 'status', 'reviewer', 'applied_at', 'reviewed_at']
    list_filter = ['status', 'applied_at', 'reviewed_at']
    search_fields = ['applicant__user__username', 'reviewer__username']
    readonly_fields = ['applied_at', 'reviewed_at']
    
    fieldsets = (
        ('申請資訊', {
            'fields': ('applicant', 'current_level', 'target_level')
        }),
        ('試煉', {
            'fields': ('trial', 'trial_record')
        }),
        ('審核', {
            'fields': ('status', 'reviewer', 'review_comment', 'reviewed_at')
        }),
    )
    
    def level_change(self, obj):
        return f"Lv.{obj.current_level} → Lv.{obj.target_level}"
    level_change.short_description = '等級變化'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        count = 0
        for req in queryset.filter(status='PENDING'):
            req.status = 'APPROVED'
            req.reviewer = request.user
            req.reviewed_at = timezone.now()
            req.save()
            
            # 更新使用者等級
            req.applicant.level = req.target_level
            req.applicant.save()
            count += 1
        
        self.message_user(request, f'已通過 {count} 個晉升申請')
    approve_requests.short_description = '通過選中的申請'
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='PENDING').update(
            status='REJECTED',
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'已拒絕 {count} 個晉升申請')
    reject_requests.short_description = '拒絕選中的申請'


@admin.register(EnhancementScroll)
class EnhancementScrollAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'quantity', 'obtained_at']
    search_fields = ['user_profile__user__username']
    readonly_fields = ['obtained_at']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'exp_reward', 'scroll_reward', 'icon_preview']
    list_filter = ['achievement_type']
    search_fields = ['name', 'description']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="50" height="50" />', obj.icon.url)
        return '-'
    icon_preview.short_description = '圖示'


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'achievement', 'unlocked_at']
    list_filter = ['achievement__achievement_type', 'unlocked_at']
    search_fields = ['user_profile__user__username', 'achievement__name']
    readonly_fields = ['unlocked_at']


class CurrentMemberInline(admin.TabularInline):
    """在隊伍管理頁面顯示當前隊員"""
    model = UserProfile
    fk_name = 'current_team'
    extra = 1  # 顯示一個空白欄位供新增
    fields = ['user', 'employee_id', 'character_class', 'level', 'experience']
    readonly_fields = ['employee_id', 'character_class', 'level', 'experience']
    autocomplete_fields = ['user']  # 使用自動完成搜尋使用者
    verbose_name = '當前隊員'
    verbose_name_plural = '當前隊員列表'
    
    def get_formset(self, request, obj=None, **kwargs):
        """自訂表單集，只顯示尚未加入隊伍的使用者"""
        formset = super().get_formset(request, obj, **kwargs)
        # 可以在這裡過濾可選擇的使用者
        return formset


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    inlines = [CurrentMemberInline]
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'description')
        }),
    )


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'team__name']
    
    fieldsets = (
        ('成員資訊', {
            'fields': ('user', 'team', 'role')
        }),
        ('時間記錄', {
            'fields': ('joined_at',)
        }),
    )


@admin.register(DailyTrialTask)
class DailyTrialTaskAdmin(admin.ModelAdmin):
    list_display = ['date', 'task_number', 'trial', 'is_active', 'created_at']
    list_filter = ['date', 'task_number', 'is_active']
    search_fields = ['trial__title']
    date_hierarchy = 'date'
    filter_horizontal = ['questions']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('date', 'task_number', 'trial', 'is_active')
        }),
        ('題目設定', {
            'fields': ('questions',)
        }),
    )


@admin.register(DailyTrialProgress)
class DailyTrialProgressAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'daily_task', 'current_hp', 'current_mp', 
                   'is_completed', 'is_passed', 'started_at']
    list_filter = ['is_completed', 'is_passed', 'daily_task__date']
    search_fields = ['user_profile__user__username', 'daily_task__trial__title']
    readonly_fields = ['started_at', 'completed_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user_profile', 'daily_task')
        }),
        ('HP/MP 狀態', {
            'fields': ('initial_hp', 'initial_mp', 'current_hp', 'current_mp')
        }),
        ('進度狀態', {
            'fields': ('is_completed', 'is_passed', 'started_at', 'completed_at')
        }),
        ('答題記錄', {
            'fields': ('answers',),
            'classes': ('collapse',)
        }),
    )
