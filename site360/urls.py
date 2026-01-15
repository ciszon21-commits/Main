from django.urls import path
from . import views

app_name = 'site360'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('project/<int:pk>/upload/', views.SceneCreateView.as_view(), name='scene_create'),
    path('project/<int:pk>/tour/', views.tour_view, name='project_tour'),
    path('project/<int:pk>/resources/', views.project_resource_list, name='project_resources'),
    path('resources/', views.all_resource_list, name='all_resources'),
    path('project/<int:pk>/tour-data/', views.project_tour_data, name='project_tour_data'),
    path('api/hotspot/save/', views.save_hotspot, name='save_hotspot'),
    path('api/hotspot/delete/<int:pk>/', views.delete_hotspot, name='delete_hotspot'),
    path('api/hotspot/move/<int:pk>/', views.move_hotspot, name='move_hotspot'),
    path('api/scene/reorder/', views.reorder_scenes, name='reorder_scenes'),
    path('api/scene/nav-update/<int:pk>/', views.update_scene_nav, name='update_scene_nav'),
    path('api/scene/set-cover/<int:pk>/', views.set_cover_image, name='set_cover_image'),
    path('api/cities/', views.get_cities, name='get_cities'),
    path('api/districts/', views.get_districts, name='get_districts'),
    path('api/video/<int:pk>/', views.serve_hotspot_video, name='serve_hotspot_video'),
    path('api/resources/', views.list_resources, name='list_resources'),
    path('api/resource/edit/<int:pk>/', views.edit_resource, name='edit_resource'),
    path('api/resource/check-updates/', views.check_resource_updates, name='check_resource_updates'),
    path('api/resource/update-reference/<int:pk>/', views.update_resource_reference, name='update_resource_reference'),
    path('api/resource/batch-update/', views.batch_update_references, name='batch_update_references'),
    path('api/resource/references/<int:pk>/', views.get_resource_references, name='get_resource_references'),
    path('api/hotspot/data/<int:pk>/', views.hotspot_data, name='hotspot_data'),
]
