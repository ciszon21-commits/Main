"""URL 設定"""
from django.urls import path
from . import views

app_name = 'carbonplbc'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('settings/', views.settings_view, name='settings'),
]
