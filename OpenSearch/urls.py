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
    path('api/search/', views.ApiSearchView.as_view(), name='api_search'),
    path('api/log-click/', views.LogClickView.as_view(), name='log_click'),
]

