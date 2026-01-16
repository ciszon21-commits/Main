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
    path('team/<int:pk>/search/', views.team_search, name='team_search'),
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
    path('topic/<int:topic_pk>/category/<int:category_pk>/item/create/', views.item_create, name='item_create_in_category'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('item/<int:pk>/edit/', views.item_update, name='item_update'),
    path('item/<int:pk>/delete/', views.item_delete, name='item_delete'),
    
    # Comment URLs
    path('item/<int:item_pk>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    
    # API URLs
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/move-item/', views.move_item, name='move_item'),
    
    # Attachment URLs
    path('item/<int:item_pk>/upload-attachment/', views.upload_item_attachment, name='upload_item_attachment'),
    path('attachment/<int:pk>/delete/', views.delete_attachment, name='delete_attachment'),
    path('comment/<int:comment_pk>/upload-attachment/', views.upload_comment_attachment, name='upload_comment_attachment'),
    path('comment-attachment/<int:pk>/delete/', views.delete_comment_attachment, name='delete_comment_attachment'),
    
    # Category Files Browser
    path('category/<int:pk>/files/', views.category_files, name='category_files'),
    
    # Quick Note URLs
    path('notes/', views.quick_note_list, name='quick_note_list'),
    path('notes/create/', views.quick_note_create, name='quick_note_create'),
    path('notes/<int:pk>/edit/', views.quick_note_edit, name='quick_note_edit'),
    path('notes/<int:pk>/delete/', views.quick_note_delete, name='quick_note_delete'),
    path('api/notes/<int:pk>/autosave/', views.quick_note_autosave, name='quick_note_autosave'),
    path('api/notes/<int:pk>/move/', views.quick_note_move_to_team, name='quick_note_move_to_team'),
    path('api/team/<int:team_pk>/topics/', views.quick_note_get_topics, name='quick_note_get_topics'),
    path('api/topic/<int:topic_pk>/categories/', views.quick_note_get_categories, name='quick_note_get_categories'),
]

