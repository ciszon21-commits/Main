from django.urls import path
from . import views

app_name = 'XrResource'

urlpatterns = [
    path('', views.dashboard, name='dashboard'), # 取代原本的 rental_register 作為首頁
    path('vr-section/', views.vr_section, name='vr_section'),
    path('gopro-section/', views.gopro_section, name='gopro_section'),
    path('equipment/save/', views.equipment_save, name='equipment_add'),
    path('equipment/save/<int:pk>/', views.equipment_save, name='equipment_edit'),
    path('bulk/save/', views.bulk_item_save, name='bulk_add'),
    path('bulk/save/<int:pk>/', views.bulk_item_save, name='bulk_edit'),
    path('delete/<str:model_name>/<int:pk>/', views.delete_item, name='delete_item'),
    path('rental/register/', views.rental_register, name='rental_register'),
    path('rental/edit/<int:pk>/', views.rental_register, name='rental_edit'),
    path('rental/list/', views.rental_list, name='rental_list'),
    path('rental/approve/<int:pk>/', views.rental_approve, name='rental_approve'),
    path('rental/reject/<int:pk>/', views.rental_reject, name='rental_reject'),
    path('rental/reset/<int:pk>/', views.rental_reset, name='rental_reset'),
    path('rental/return/<int:pk>/', views.rental_return, name='rental_return'),
    path('rental/return/reset/<int:pk>/', views.reset_rental_return, name='reset_rental_return'),
]
