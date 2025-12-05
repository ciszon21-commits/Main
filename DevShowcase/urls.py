from django.urls import path
from . import views

app_name = 'devshowcase'

urlpatterns = [
    path('', views.AchievementListView.as_view(), name='achievement_list'),
    path('achievement/<int:pk>/', views.AchievementDetailView.as_view(), name='achievement_detail'),
    path('achievement/create/', views.AchievementCreateView.as_view(), name='achievement_create'),
    path('achievement/<int:pk>/edit/', views.AchievementUpdateView.as_view(), name='achievement_update'),
    path('achievement/<int:pk>/comment/', views.comment_create, name='comment_create'),
]
