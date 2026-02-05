from django.urls import path
from . import views

app_name = 'lunchorder'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('statistics/', views.order_statistics, name='order_statistics'),
    path('api/menu-items/<int:restaurant_id>/', views.get_menu_items, name='get_menu_items'),
]
