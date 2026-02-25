"""
URL configuration for GravityPipeCalc app
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='gravity_pipe_home'),
    path('calculate/type1/', views.calculate_type1, name='calculate_type1'),
    path('calculate/type2/', views.calculate_type2, name='calculate_type2'),
    path('calculate/type3/', views.calculate_type3, name='calculate_type3'),
    path('calculate/type4/', views.calculate_type4, name='calculate_type4'),
    path('calculate/type5/', views.calculate_type5, name='calculate_type5'),
    path('calculate/type6/', views.calculate_type6, name='calculate_type6'),
    path('calculate/type7/', views.calculate_type7, name='calculate_type7'),
    path('calculate/type8/', views.calculate_type8, name='calculate_type8'),
]
