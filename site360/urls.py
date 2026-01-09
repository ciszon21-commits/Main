from django.urls import path
from . import views

app_name = 'site360'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<int:pk>/tour/', views.tour_view, name='project_tour'),
    path('project/<int:pk>/tour-data/', views.project_tour_data, name='project_tour_data'),
    path('api/hotspot/save/', views.save_hotspot, name='save_hotspot'),
    path('api/hotspot/delete/<int:pk>/', views.delete_hotspot, name='delete_hotspot'),
    path('api/scene/reorder/', views.reorder_scenes, name='reorder_scenes'),
]
