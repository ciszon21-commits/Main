from django.urls import path
from . import views

app_name = 'patent_registry'

urlpatterns = [
    # 公開頁面 - 首頁
    path('', views.PublicPatentListView.as_view(), name='public_list'),
    
    # 專利申請管理
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/create/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_update'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),
    
    # 答辯管理
    path('applications/<int:app_id>/rebuttal/create/', views.RebuttalCreateView.as_view(), name='rebuttal_create'),
    path('rebuttal/<int:pk>/delete/', views.RebuttalDeleteView.as_view(), name='rebuttal_delete'),
    
    # 審核結果
    path('applications/<int:pk>/grant/', views.GrantApplicationView.as_view(), name='application_grant'),
    path('applications/<int:pk>/reject/', views.RejectApplicationView.as_view(), name='application_reject'),
    
    # 已取得專利
    path('granted/<int:pk>/', views.GrantedPatentDetailView.as_view(), name='granted_detail'),
    path('granted/<int:pk>/edit/', views.GrantedPatentUpdateView.as_view(), name='granted_update'),
    
    # 年費核銷管理
    path('annuity/', views.AnnuityListView.as_view(), name='annuity_list'),
    path('granted/<int:patent_id>/annuity/create/', views.AnnuityCreateView.as_view(), name='annuity_create'),
    path('annuity/<int:pk>/delete/', views.AnnuityDeleteView.as_view(), name='annuity_delete'),
    
    # 專利管理員設定 (僅超級使用者)
    path('admin-settings/', views.PatentAdminListView.as_view(), name='admin_settings'),
    path('admin-settings/add/', views.PatentAdminCreateView.as_view(), name='admin_add'),
    path('admin-settings/<int:pk>/delete/', views.PatentAdminDeleteView.as_view(), name='admin_delete'),
    
    # API
    path('api/search-users/', views.user_search_api, name='api_search_users'),
]
