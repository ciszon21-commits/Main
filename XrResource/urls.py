from django.urls import path
from . import views

app_name = 'XrResource'

urlpatterns = [
    path('', views.vr_section, name='dashboard'), # 把原本的根目錄改為 VR 專區，延用名稱以減少模板改動
    path('vr-section/', views.vr_section, name='vr_section'),
    path('gopro-section/', views.gopro_section, name='gopro_section'),
    path('equipment/save/', views.equipment_save, name='equipment_add'),
    path('equipment/save/<int:pk>/', views.equipment_save, name='equipment_edit'),
    path('bulk/save/', views.bulk_item_save, name='bulk_add'),
    path('bulk/save/<int:pk>/', views.bulk_item_save, name='bulk_edit'),
    path('delete/<str:model_name>/<int:pk>/', views.delete_item, name='delete_item'),
]
