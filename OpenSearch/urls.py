"""
OpenSearch URL Configuration
"""
from django.urls import path
from . import views

app_name = 'opensearch'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('advanced/', views.AdvancedSearchView.as_view(), name='advanced'),
    path('ai-chat/', views.AIChatView.as_view(), name='ai_chat'),
    path('api/search/', views.ApiSearchView.as_view(), name='api_search'),
    path('api/log-click/', views.LogClickView.as_view(), name='log_click'),
    path('api/ai-chat/', views.AIChatApiView.as_view(), name='api_ai_chat'),
    path('api/ai-chat/<int:chat_id>/', views.AIChatHistoryApiView.as_view(), name='api_ai_chat_history'),
]

