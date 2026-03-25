from django.urls import path
from . import views

app_name = 'EnergyMap'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('map/', views.map_view, name='map'),
    path('api/energy-data/', views.api_energy_data, name='api_energy_data'),
    path('api/plant-locations/', views.api_plant_locations, name='api_plant_locations'),
]
