from django.urls import path
from . import views

app_name = 'bidqa'

urlpatterns = [
    # 標案
    path('', views.bid_list, name='bid_list'),
    path('bid/create/', views.bid_create, name='bid_create'),
    path('bid/<int:pk>/', views.bid_detail, name='bid_detail'),
    path('bid/<int:pk>/edit/', views.bid_update, name='bid_update'),
    path('bid/<int:pk>/delete/', views.bid_delete, name='bid_delete'),
    
    # 標案委員
    path('bid/<int:bid_pk>/add-committee/', views.add_committee_to_bid, name='add_committee_to_bid'),
    path('bid/<int:bid_pk>/remove-committee/<int:committee_pk>/', views.remove_committee_from_bid, name='remove_committee_from_bid'),
    
    # 標案文件
    path('bid/<int:bid_pk>/upload/', views.file_upload, name='file_upload'),
    path('file/<int:pk>/download/', views.file_download, name='file_download'),
    path('file/<int:pk>/delete/', views.file_delete, name='file_delete'),
    path('file/<int:pk>/logs/', views.file_download_logs, name='file_download_logs'),
    
    # 委員
    path('committees/', views.committee_list, name='committee_list'),
    path('committees/import/', views.import_committees, name='import_committees'),
    path('committee/create/', views.committee_create, name='committee_create'),
    path('committee/<int:pk>/', views.committee_detail, name='committee_detail'),
    path('committee/<int:pk>/edit/', views.committee_update, name='committee_update'),
    
    # 問答
    path('question/create/<int:bid_committee_pk>/', views.question_create, name='question_create'),
    path('question/<int:pk>/edit/', views.question_update, name='question_update'),
    path('question/<int:pk>/delete/', views.question_delete, name='question_delete'),
    
    # 快速查詢
    path('search/', views.quick_search, name='quick_search'),
    
    # API
    path('api/committees/search/', views.search_committees_api, name='search_committees_api'),
    path('api/committees/search-by-name/', views.search_committees_by_name_api, name='search_committees_by_name_api'),
]


