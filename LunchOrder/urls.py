from django.urls import path
from . import views

app_name = 'lunchorder'

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('list/', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('delete/<int:order_id>/', views.order_delete, name='order_delete'),
    path('statistics/', views.order_statistics, name='order_statistics'),
    path('api/set-schedule/', views.set_daily_restaurant, name='set_daily_restaurant'),
    path('api/menu-items/<int:restaurant_id>/', views.get_menu_items, name='get_menu_items'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:restaurant_id>/update-menu/', views.restaurant_update_menu, name='restaurant_update_menu'),
    path('api/restaurants/<int:restaurant_id>/menu-item/add/', views.menu_item_add, name='menu_item_add'),
    path('api/restaurants/<int:restaurant_id>/menu-item/<int:item_id>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('api/restaurants/<int:restaurant_id>/menu-item/delete/', views.menu_item_delete, name='menu_item_delete'),
    path('restaurants/<int:restaurant_id>/delete/', views.restaurant_delete, name='restaurant_delete'),
    path('payment/upload/', views.payment_upload, name='payment_upload'),
]
