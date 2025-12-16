from django.urls import path, register_converter
from . import views


class UnicodeSlugConverter:
    """自定義路徑轉換器以支援 Unicode slug（包含中文）"""
    regex = r'[\w-]+'
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value


# 註冊自定義轉換器
register_converter(UnicodeSlugConverter, 'uslug')

app_name = 'tutorialhub'

urlpatterns = [
    # 教材列表與建立
    path('', views.TutorialListView.as_view(), name='tutorial_list'),
    path('create/', views.TutorialCreateView.as_view(), name='tutorial_create'),
    path('my/', views.my_tutorials, name='my_tutorials'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # 教材詳情與編輯
    path('<uslug:slug>/', views.TutorialDetailView.as_view(), name='tutorial_detail'),
    path('<uslug:slug>/edit/', views.TutorialUpdateView.as_view(), name='tutorial_update'),
    path('<uslug:slug>/delete/', views.TutorialDeleteView.as_view(), name='tutorial_delete'),
    
    # 步驟管理
    path('<uslug:slug>/steps/', views.tutorial_edit_steps, name='tutorial_edit_steps'),
    path('<uslug:slug>/steps/add/', views.add_step, name='add_step'),
    path('<uslug:slug>/steps/<int:step_id>/delete/', views.delete_step, name='delete_step'),
    path('<uslug:slug>/steps/<int:step_id>/update/', views.update_step, name='update_step'),
    path('<uslug:slug>/steps/<int:step_id>/snippets/', views.step_edit_snippets, name='step_edit_snippets'),
    path('<uslug:slug>/steps/reorder/', views.reorder_steps, name='reorder_steps'),
    
    # 片段管理
    path('<uslug:slug>/snippets/<int:step_id>/add/', views.add_snippet, name='add_snippet'),
    path('<uslug:slug>/snippets/<int:snippet_id>/delete/', views.delete_snippet, name='delete_snippet'),
    path('<uslug:slug>/snippets/<int:snippet_id>/update/', views.update_snippet, name='update_snippet'),
    path('<uslug:slug>/snippets/reorder/', views.reorder_snippets, name='reorder_snippets'),
    
    # API 端點
    path('api/reading-time/', views.update_reading_time, name='update_reading_time'),
    path('api/questions/', views.create_question, name='create_question'),
    path('api/answers/', views.create_answer, name='create_answer'),
    path('api/questions/<int:question_id>/toggle/', views.toggle_question_resolved, name='toggle_question'),
    path('api/users/search/', views.search_users, name='search_users'),
    
    # 貢獻者管理
    path('<uslug:slug>/contributors/', views.manage_contributors, name='manage_contributors'),
    path('<uslug:slug>/contributors/add/', views.add_contributor, name='add_contributor'),
    path('<uslug:slug>/contributors/<int:user_id>/remove/', views.remove_contributor, name='remove_contributor'),
    
    # 使用者頁面
    path('user/<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
]

