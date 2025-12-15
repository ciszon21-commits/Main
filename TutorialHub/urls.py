from django.urls import path
from . import views

app_name = 'tutorialhub'

urlpatterns = [
    # 教材相關
    path('', views.TutorialListView.as_view(), name='tutorial_list'),
    path('create/', views.TutorialCreateView.as_view(), name='tutorial_create'),
    path('<slug:slug>/', views.TutorialDetailView.as_view(), name='tutorial_detail'),
    path('<slug:slug>/edit/', views.TutorialUpdateView.as_view(), name='tutorial_update'),
    
    # API 端點
    path('api/reading-time/', views.update_reading_time, name='update_reading_time'),
    path('api/questions/', views.create_question, name='create_question'),
    path('api/answers/', views.create_answer, name='create_answer'),
    path('api/questions/<int:question_id>/toggle/', views.toggle_question_resolved, name='toggle_question'),
    
    # 使用者與統計
    path('user/<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
    path('analytics/', views.analytics_view, name='analytics'),
]
