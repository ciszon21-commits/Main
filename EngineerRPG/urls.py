from django.urls import path
from . import views

app_name = 'engineer_rpg'

urlpatterns = [
    # 註冊與登入 (已移除，改由外部與白名單管理)
    # path('register/', views.user_register, name='register'),
    # path('login/', views.user_login, name='login'),
    
    # 白名單管理
    path('admin-panel/whitelist/', views.admin_whitelist_view, name='admin_whitelist'),
    path('admin-panel/whitelist/add/', views.admin_whitelist_add, name='admin_whitelist_add'),
    path('admin-panel/whitelist/<int:whitelist_id>/delete/', views.admin_whitelist_delete, name='admin_whitelist_delete'),
    path('api/search-users/', views.api_search_users, name='api_search_users'),
    
    # 首頁與儀表板
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('select-class/', views.select_class, name='select_class'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # 技能樹
    path('skill-tree/', views.skill_tree, name='skill_tree'),
    path('skill/<int:skill_id>/', views.skill_detail, name='skill_detail'),
    path('skill/<int:skill_id>/start/', views.start_learning, name='start_learning'),
    path('skill/<int:skill_id>/complete/', views.complete_skill, name='complete_skill'),
    
    # 裝備系統
    path('equipment/', views.equipment_inventory, name='equipment_inventory'),
    path('equipment/<int:user_equipment_id>/equip/', views.equip_item, name='equip_item'),
    path('equipment/<int:user_equipment_id>/unequip/', views.unequip_item, name='unequip_item'),
    path('equipment/<int:user_equipment_id>/enhance/', views.enhance_equipment, name='enhance_equipment'),
    
    # 道具系統
    path('inventory/', views.item_inventory, name='item_inventory'),
    path('item/<int:user_item_id>/use/', views.use_item, name='use_item'),
    path('item/<int:user_item_id>/consume/', views.api_consume_item, name='api_consume_item'),
    
    # 試煉系統
    path('training-hall/', views.training_hub, name='training_hub'),
    path('daily-trial/', views.daily_trial_list, name='daily_trial_list'),
    path('daily-trial/<int:task_id>/start/', views.start_daily_trial, name='start_daily_trial'),
    path('daily-trial/<int:task_id>/chest/<int:chest_index>/open/', views.open_daily_chest, name='open_daily_chest'),
    path('dungeons/', views.dungeon_list, name='dungeon_list'),
    path('trial/records/', views.trial_record_list, name='trial_record_list'),
    path('trial/record/<int:record_id>/', views.trial_record_detail, name='trial_record_detail'),
    path('trial/<int:trial_id>/', views.trial_detail, name='trial_detail'),
    path('trial/<int:trial_id>/start/', views.start_trial, name='start_trial'),
    path('trial/<int:trial_id>/submit-answer/', views.submit_answer, name='submit_answer'),
    path('trial/<int:trial_id>/next-question/', views.next_question, name='next_question'),
    path('trial/<int:trial_id>/submit/', views.submit_trial, name='submit_trial'),
    path('trial/<int:trial_id>/uav-eliminate/', views.uav_eliminate_option, name='uav_eliminate_option'),
    path('trial/<int:trial_id>/vr-reveal/', views.vr_reveal_answer, name='vr_reveal_answer'),
    path('trial/<int:trial_id>/camera-rewind/', views.camera_rewind, name='camera_rewind'),
    
    # 升階系統
    path('promotion/apply/', views.apply_promotion, name='apply_promotion'),
    path('promotion/trial/<int:request_id>/', views.promotion_trial, name='promotion_trial'),
    
    # 排行榜
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # 主管介面（公會會長）
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/requests/', views.promotion_requests, name='promotion_requests'),
    path('manager/request/<int:request_id>/', views.review_request, name='review_request'),
    path('manager/request/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('manager/request/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('manager/skills/', views.manage_skill_tree, name='manage_skill_tree'),
    path('manager/questions/', views.manage_questions, name='manage_questions'),
    
    # API endpoints - Moved to specific section below
    
    # 管理員介面（創世神）
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.user_management, name='user_management'),

    # 公會系統
    path('guild/', views.guild_dashboard, name='guild_dashboard'),  # 公會大廳
    path('guild/announcements/', views.guild_announcement_list, name='guild_announcement_list'),  # 公告欄列表
    path('guild/announcement/create/', views.guild_announcement_create, name='guild_announcement_create'),  # 發布公告（管理員專用）
    path('guild/announcement/<int:post_id>/edit/', views.guild_announcement_edit, name='guild_announcement_edit'),  # 編輯公告
    path('guild/announcement/<int:post_id>/delete/', views.guild_announcement_delete, name='guild_announcement_delete'),  # 刪除公告
    path('guild/exchange/', views.guild_exchange_list, name='guild_exchange_list'),  # 交流區列表
    path('guild/exchange/create/', views.guild_post_create, name='guild_post_create'),  # 發文
    path('guild/exchange/<int:post_id>/', views.guild_post_detail, name='guild_post_detail'),  # 文章詳情
    path('admin-panel/users/create/', views.create_user, name='create_user'),
    path('admin-panel/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('admin-panel/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin-panel/questions/', views.question_management, name='question_management'),
    path('admin-panel/questions/batch/', views.batch_manage_questions, name='batch_manage_questions'),
    path('admin-panel/questions/create/', views.create_question, name='create_question'),
    path('admin-panel/questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('admin-panel/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('admin-panel/courses/', views.course_management, name='course_management'),
    path('admin-panel/courses/create/', views.create_course, name='create_course'),
    path('admin-panel/courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('admin-panel/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('admin-panel/courses/batch/', views.batch_manage_courses, name='batch_manage_courses'),
    path('admin-panel/courses/import/', views.import_courses, name='import_courses'),
    path('admin-panel/courses/template/<str:format>/', views.download_course_template, name='download_course_template'),
    
    # Study & Exam
    path('courses/<int:course_id>/study/', views.course_study, name='course_study'),
    path('courses/<int:course_id>/exam/', views.course_exam, name='course_exam'),
    path('courses/<int:course_id>/exam/submit/', views.submit_course_exam, name='submit_course_exam'),
    path('admin-panel/categories/', views.category_management, name='category_management'),
    path('admin-panel/dungeons/', views.dungeon_management, name='dungeon_management'),
    path('admin-panel/dungeons/create/', views.create_dungeon, name='create_dungeon'),
    path('admin-panel/dungeons/<int:dungeon_id>/edit/', views.edit_dungeon, name='edit_dungeon'),
    path('admin-panel/questions/import/', views.import_questions_view, name='import_questions'),
    path('admin-panel/questions/template/<str:format>/', views.download_template, name='download_template'),
    path('admin-panel/reset-daily-trials/', views.reset_daily_trials, name='reset_daily_trials'),
    path('admin-panel/skill-tree-editor/', views.skill_tree_editor, name='skill_tree_editor'),
    
    # 隊伍管理（管理中心）
    path('admin-panel/teams/', views.team_management, name='team_management'),
    path('admin-panel/teams/create/', views.create_team, name='create_team'),
    path('admin-panel/teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('admin-panel/teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('admin-panel/teams/<int:team_id>/members/', views.manage_team_members, name='manage_team_members'),
    
    # API endpoints (for AJAX)
    path('api/user-stats/', views.api_user_stats, name='api_user_stats'),
    path('api/skill-tree-data/', views.api_skill_tree_data, name='api_skill_tree_data'),
    path('api/skill-editor/data/', views.api_skill_editor_data, name='api_skill_editor_data'),
    path('api/skill-editor/save-layout/', views.api_save_skill_layout, name='api_save_skill_layout'),
    path('api/skill-editor/node/save/', views.api_save_skill_node, name='api_save_skill_node'),
    path('api/skill-editor/node/delete/', views.api_delete_skill_node, name='api_delete_skill_node'),
    path('api/skill-editor/course/manage/', views.api_manage_skill_course, name='api_manage_skill_course'),
    path('api/skill-tree/auto-layout/', views.api_auto_layout_skill_tree, name='api_auto_layout_skill_tree'),
    path('api/skill-editor/auto-distribute/', views.api_auto_distribute_xp, name='api_auto_distribute_xp'),
    
    # 隊伍管理
    path('team/', views.team_dashboard, name='team_dashboard'),
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/member/<int:member_id>/', views.team_member_detail, name='team_member_detail'),
    path('team/<int:team_id>/manage/', views.team_manage_members, name='team_manage_members'),
    path('team/<int:team_id>/add-member/', views.team_add_member, name='team_add_member'),
    path('team/<int:team_id>/remove-member/<int:member_id>/', views.team_remove_member, name='team_remove_member'),
    
    # 成員詳細資料（公會會長專用）
    path('member/<int:member_id>/profile/', views.member_profile_detail, name='member_profile_detail'),
]
