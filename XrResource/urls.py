from django.urls import path
from . import views

app_name = 'XrResource'

urlpatterns = [
    path('', views.vr_section, name='dashboard'), # 把原本的根目錄改為 VR 專區，延用名稱以減少模板改動
    path('vr-section/', views.vr_section, name='vr_section'),
    path('gopro-section/', views.gopro_section, name='gopro_section'),
    path('delete/<str:model_name>/<int:pk>/', views.delete_item, name='delete_item'),
]
