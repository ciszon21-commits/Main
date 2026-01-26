from django.urls import path
from . import views

app_name = 'sinochat'

urlpatterns = [
    # 頁面路由
    path('', views.chat_room_list, name='room_list'),
    path('room/<int:room_id>/', views.chat_room_detail, name='room_detail'),
    path('create/', views.create_room, name='create_room'),

    # API 路由
    path('api/room/<int:room_id>/send/', views.send_message, name='send_message'),
    path('api/room/<int:room_id>/messages/', views.get_messages, name='get_messages'),
    path('api/room/<int:room_id>/invite/', views.invite_members, name='invite_members'),
    path('api/room/<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('api/room/<int:room_id>/download-logs/', views.download_logs, name='download_logs'),
    path('api/users/search/', views.search_users, name='search_users'),
    path('api/files/<int:file_id>/', views.file_access, name='file_access'),
]
