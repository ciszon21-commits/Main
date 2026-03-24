"""
URL configuration for WellDrawdown app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='well_drawdown_home'),
    path('calculate/', views.calculate, name='well_drawdown_calculate'),
    path('forward/', views.forward_page, name='well_drawdown_forward'),
    path('forward_calculate/', views.calculate_forward, name='well_drawdown_calculate_forward'),
]
