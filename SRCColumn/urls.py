"""
URL configuration for SRCColumn app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='src_column_home'),
    path('calculate/', views.calculate, name='src_column_calculate'),
    path('download/', views.download_docx, name='src_column_download'),
]
