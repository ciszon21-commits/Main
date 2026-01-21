"""
GeoDataHub URLs
================
URL 路由配置
"""

from django.urls import path
from . import views

app_name = 'geodatahub'

urlpatterns = [
    # 主頁面
    path('', views.MapView.as_view(), name='map'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('mark/', views.MapMarkView.as_view(), name='map_mark'),
    
    # 資料來源 CRUD
    path('sources/', views.DataSourceListView.as_view(), name='source_list'),
    path('sources/create/', views.DataSourceCreateView.as_view(), name='source_create'),
    path('sources/<int:pk>/', views.DataSourceDetailView.as_view(), name='source_detail'),
    path('sources/<int:pk>/edit/', views.DataSourceUpdateView.as_view(), name='source_update'),
    path('sources/<int:pk>/delete/', views.DataSourceDeleteView.as_view(), name='source_delete'),
    path('api/sources/<int:pk>/delete/', views.DataSourceDeleteAPI.as_view(), name='api_source_delete'),
    
    # API 端點
    path('api/categories/', views.CategoryListAPI.as_view(), name='api_categories'),
    path('api/search/', views.GeoSearchAPI.as_view(), name='api_search'),
    path('api/count/', views.GeoCountAPI.as_view(), name='api_count'),
    path('api/geocode/', views.GeocodeAPI.as_view(), name='api_geocode'),
    path('api/reverse-geocode/', views.ReverseGeocodeAPI.as_view(), name='api_reverse_geocode'),
    path('api/tags/', views.TagListAPI.as_view(), name='api_tags'),
    path('api/log-click/', views.GeoClickLogAPI.as_view(), name='api_log_click'),
    
    # OpenSearch 地理搜尋 API
    path('api/opensearch/geo/', views.OpenSearchGeoSearchAPI.as_view(), name='api_opensearch_geo'),
    
    # 分類管理 (僅限 Superuser)
    path('categories/', views.CategoryManageView.as_view(), name='category_manage'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
]

