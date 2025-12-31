from django.urls import path
from . import views

app_name = 'programdb'

urlpatterns = [
    # Team URLs
    path('', views.team_list, name='team_list'),
    path('team/create/', views.team_create, name='team_create'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
    path('team/<int:pk>/edit/', views.team_update, name='team_update'),
    path('team/<int:pk>/members/', views.team_members, name='team_members'),
    path('team/<int:pk>/add-member/', views.add_member, name='add_member'),
    path('team/<int:pk>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
    path('team/<int:pk>/add-db-server/', views.add_db_server, name='add_db_server'),
    path('team/<int:pk>/delete-db-server/<int:server_id>/', views.delete_db_server, name='delete_db_server'),
    path('team/<int:pk>/add-platform-api/', views.add_platform_api, name='add_platform_api'),
    path('team/<int:pk>/delete-platform-api/<int:api_id>/', views.delete_platform_api, name='delete_platform_api'),
    
    # Program URLs
    path('team/<int:team_pk>/program/create/', views.program_create, name='program_create'),
    path('program/<int:pk>/', views.program_detail, name='program_detail'),
    path('program/<int:pk>/edit/', views.program_update, name='program_update'),
    path('program/<int:pk>/delete/', views.program_delete, name='program_delete'),
    
    # Design Documentation URLs
    path('program/<int:program_pk>/design-doc/create/', views.design_doc_create, name='design_doc_create'),
    path('design-doc/<int:pk>/', views.design_doc_detail, name='design_doc_detail'),
    path('design-doc/<int:pk>/edit/', views.design_doc_update, name='design_doc_update'),
    path('design-doc/<int:pk>/delete/', views.design_doc_delete, name='design_doc_delete'),
    path('design-doc/<int:pk>/parse/', views.design_doc_parse, name='design_doc_parse'),
    path('design-doc/<int:pk>/download/', views.design_doc_mermaid_download, name='design_doc_download'),
    path('design-doc/<int:doc_pk>/tables/edit/', views.design_table_edit, name='design_table_edit'),
    path('design-table/<int:table_pk>/fields/edit/', views.design_field_edit, name='design_field_edit'),
    
    # Virtual Employee URLs
    path('team/<int:team_pk>/virtual-employee/create/', views.virtual_employee_create, name='virtual_employee_create'),
    path('virtual-employee/<int:pk>/edit/', views.virtual_employee_update, name='virtual_employee_update'),
    path('virtual-employee/<int:pk>/delete/', views.virtual_employee_delete, name='virtual_employee_delete'),
    path('virtual-employee/<int:pk>/retire/', views.virtual_employee_retire, name='virtual_employee_retire'),
    
    # API URLs
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/team/<int:pk>/server/<int:server_id>/programs/', views.get_server_programs, name='get_server_programs'),
    path('api/team/<int:pk>/platform-api/<int:api_id>/programs/', views.get_api_programs, name='get_api_programs'),
]

