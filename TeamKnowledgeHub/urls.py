from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    # Team URLs
    path('', views.team_list, name='team_list'),
    path('team/create/', views.team_create, name='team_create'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
    path('team/<int:pk>/edit/', views.team_update, name='team_update'),
    path('team/<int:pk>/members/', views.team_members, name='team_members'),
    path('team/<int:pk>/add-member/', views.add_member, name='add_member'),
    path('team/<int:pk>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
    
    # Topic URLs
    path('team/<int:team_pk>/topic/create/', views.topic_create, name='topic_create'),
    path('topic/<int:pk>/edit/', views.topic_update, name='topic_update'),
    path('topic/<int:pk>/delete/', views.topic_delete, name='topic_delete'),
    
    # Category URLs
    path('topic/<int:topic_pk>/category/create/', views.category_create, name='category_create'),
    path('topic/<int:topic_pk>/category/manage/', views.category_manage, name='category_manage'),
    path('category/<int:pk>/edit/', views.category_update, name='category_update'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Item URLs
    path('topic/<int:topic_pk>/item/create/', views.item_create, name='item_create'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('item/<int:pk>/edit/', views.item_update, name='item_update'),
    path('item/<int:pk>/delete/', views.item_delete, name='item_delete'),
    
    # Comment URLs
    path('item/<int:item_pk>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    
    # API URLs
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/move-item/', views.move_item, name='move_item'),
]
