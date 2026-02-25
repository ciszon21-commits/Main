from django.urls import path
from . import views

app_name = 'NewsInsight'

urlpatterns = [
    path('', views.index, name='index'),
    path('export/', views.export_excel, name='export_excel'),
]
