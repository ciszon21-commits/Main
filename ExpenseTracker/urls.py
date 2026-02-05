from django.urls import path
from . import views

app_name = 'expense_tracker'

urlpatterns = [
    # 記帳 CRUD
    path('', views.expense_list, name='expense_list'),
    path('create/', views.expense_create, name='expense_create'),
    path('<int:pk>/edit/', views.expense_update, name='expense_update'),
    path('<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    # 統計與結算
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('settlement/', views.settlement, name='settlement'),
    
    # 類型管理
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    
    # 參與者管理
    path('participants/', views.participant_list, name='participant_list'),
    path('participants/<int:pk>/delete/', views.participant_delete, name='participant_delete'),

    # 匯出
    path('export/csv/', views.export_expenses_csv, name='export_expenses_csv'),
]
