from django.urls import path
from . import views

app_name = 'devshowcase'

urlpatterns = [
    path('', views.AchievementListView.as_view(), name='achievement_list'),
    path('achievement/<int:pk>/', views.AchievementDetailView.as_view(), name='achievement_detail'),
    path('achievement/create/', views.AchievementCreateView.as_view(), name='achievement_create'),
    path('achievement/<int:pk>/edit/', views.AchievementUpdateView.as_view(), name='achievement_update'),
    path('achievement/<int:pk>/comment/', views.comment_create, name='comment_create'),

    # User search API
    path('users/search/', views.user_search, name='user_search'),

    # Category Management (Staff Only)
    path('category/', views.CategoryListView.as_view(), name='category_list'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]
