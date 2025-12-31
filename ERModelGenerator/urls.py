from django.urls import path
from . import views

app_name = 'er_model'

urlpatterns = [
    # 主頁面
    path('', views.er_diagram_view, name='diagram'),
    
    # API endpoints
    path('api/mermaid/', views.api_mermaid_code, name='api_mermaid'),
    path('api/apps/', views.api_app_list, name='api_apps'),
    path('api/apps/<str:app_label>/models/', views.api_app_models, name='api_app_models'),
    
    # 下載
    path('download/', views.download_mermaid, name='download'),
]
