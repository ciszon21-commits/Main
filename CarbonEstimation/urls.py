from django.urls import path
from . import views

urlpatterns = [
    # Change root to scenario management
    path('', views.scenario_list, name='home'),
    path('hidden-scenarios/', views.hidden_scenario_list, name='hidden_scenarios'),
    path('calculator/', views.calculator_view, name='calculator'),
    
    # API endpoints
    path('api/scenarios/', views.create_scenario, name='create_scenario'),
    path('api/scenarios/<int:scenario_id>/update/', views.update_scenario, name='update_scenario'),
    path('api/scenarios/<int:scenario_id>/', views.delete_scenario, name='delete_scenario'),
    path('api/scenarios/<int:scenario_id>/save-category/', views.save_category_data, name='save_category'),
    path('api/scenarios/<int:scenario_id>/load/', views.load_scenario, name='load_scenario'),
    path('api/scenarios/<int:scenario_id>/restore/', views.restore_scenario, name='restore_scenario'),
    path('api/scenarios/<int:scenario_id>/collaborators/', views.manage_collaborators, name='manage_collaborators'),
   path('api/users/search/', views.search_users, name='search_users'),
    
    # Section calculator routes
    path('section-calculator/', views.section_calculator_view, name='section_calculator'),
    path('api/scenarios/<int:scenario_id>/save-section/', views.save_section_data, name='save_section'),
    path('api/scenarios/<int:scenario_id>/load-section/', views.load_section_scenario, name='load_section_scenario'),
        
    # Scenario management
    path('scenarios/', views.scenario_list, name='scenario_list'),
]
