from django.urls import path
from . import views

urlpatterns = [
    # Change root to scenario management
    path('', views.scenario_list, name='home'),
    path('calculator/', views.calculator_view, name='calculator'),
    
    # API endpoints
    path('api/scenarios/', views.create_scenario, name='create_scenario'),
    path('api/scenarios/<int:scenario_id>/update/', views.update_scenario, name='update_scenario'),
    path('api/scenarios/<int:scenario_id>/', views.delete_scenario, name='delete_scenario'),
    path('api/scenarios/<int:scenario_id>/save-category/', views.save_category_data, name='save_category'),
    path('api/scenarios/<int:scenario_id>/load/', views.load_scenario, name='load_scenario'),
    path('api/scenarios/<int:scenario_id>/collaborators/', views.manage_collaborators, name='manage_collaborators'),
    path('api/users/search/', views.search_users, name='search_users'),
        
    # Scenario management
    path('scenarios/', views.scenario_list, name='scenario_list'),
]
