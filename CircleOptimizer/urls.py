"""
URL Configuration for Circle Optimizer App
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'circle_optimizer'

# DRF Router
router = DefaultRouter()
router.register(r'shapes', views.ShapeViewSet, basename='shape')
router.register(r'configs', views.CircleConfigViewSet, basename='config')
router.register(r'circles', views.CircleViewSet, basename='circle')

urlpatterns = [
    # 首頁
    path('', views.home, name='home'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
