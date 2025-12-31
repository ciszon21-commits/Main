"""
EVCodeSigning URLs - 路由設定
"""
from django.urls import path
from .views import (
    EVCodeSigningInfoView,
    PublicSigningRecordListView,
    SigningRequestListView,
    SigningRequestDetailView,
    SigningRequestCreateView,
    AdminPendingListView,
    SigningAdminManageView,
    download_original_file,
    download_signed_file,
    upload_signed_file,
    complete_signing,
    reject_request,
    search_users_for_admin,
    add_signing_admin,
    remove_signing_admin,
    toggle_signing_admin,
)

app_name = 'evcodesigning'

urlpatterns = [
    # 說明頁面
    path('', EVCodeSigningInfoView.as_view(), name='info'),
    
    # 簽章記錄公開列表
    path('records/', PublicSigningRecordListView.as_view(), name='public_records'),
    
    # 申請列表與詳情（需登入）
    path('requests/', SigningRequestListView.as_view(), name='request_list'),
    path('requests/create/', SigningRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', SigningRequestDetailView.as_view(), name='request_detail'),
    
    # 簽章管理員功能
    path('admin/pending/', AdminPendingListView.as_view(), name='admin_pending'),
    
    # 檔案操作
    path('file/<int:pk>/download/', download_original_file, name='download_original'),
    path('file/<int:pk>/download-signed/', download_signed_file, name='download_signed'),
    path('file/<int:pk>/upload-signed/', upload_signed_file, name='upload_signed'),
    
    # 申請操作
    path('requests/<int:pk>/complete/', complete_signing, name='complete_signing'),
    path('requests/<int:pk>/reject/', reject_request, name='reject_request'),
    
    # 簽章管理員管理（僅 superuser）
    path('superuser/admins/', SigningAdminManageView.as_view(), name='admin_manage'),
    path('superuser/admins/search/', search_users_for_admin, name='search_users_for_admin'),
    path('superuser/admins/add/', add_signing_admin, name='add_signing_admin'),
    path('superuser/admins/<int:pk>/remove/', remove_signing_admin, name='remove_signing_admin'),
    path('superuser/admins/<int:pk>/toggle/', toggle_signing_admin, name='toggle_signing_admin'),
]
