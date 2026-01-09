
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.inlet_design, name='inlet_design'),
    path('api/calculate/', views.calculate_view, name='step_one_input'),
    path('api/ogee/', views.ogee, name='ogee'),
    path('api/horseshoe/', views.horseshoe, name='horseshoe'),
    path('api/horseshoe_supercritical_table/',views.horseshoe_supercritical_table,name='horseshoe_supercritical_table'),
    path('api/horseshoe_subcritical_table/',views.horseshoe_subcritical_table,name='horseshoe_subcritical_table'),
    path('api/round/',views.round,name='round'),
    path('api/round_supercritical_table/',views.round_supercritical_table,name='round_supercritical_table'),
    path('api/round_subcritical_table/',views.round_subcritical_table,name='round_subcritical_table'),
    path('api/inlet_transition_table/',views.inlet_transition_table,name='inlet_transition_table'),
    path('api/inlet_transition_initial_table/',views.inlet_transition_initial_table,name='inlet_transition_initial_table'),
    path('api/inlet_diagram/',views.inlet_diagram,name='inlet_diagram'),
    path('api/transition_shape/',views.transition_shape,name='transition_shape'),
    path('api/transition_figure/',views.transition_figure,name='transition_figure'),
    path('api/water_level/',views.water_level,name='water_level')
]