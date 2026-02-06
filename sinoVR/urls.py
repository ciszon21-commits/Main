from django.urls import path
from . import views

app_name = 'sinoVR'

urlpatterns = [
    path('', views.SceneListView.as_view(), name='scene_list'),
    path('create/', views.SceneCreateView.as_view(), name='scene_create'),
    path('scene/<int:pk>/', views.SceneDetailView.as_view(), name='scene_detail'),
    path('scene/<int:pk>/view/', views.SceneViewerView.as_view(), name='scene_view'),
    path('api/scene/<int:pk>/save/', views.SceneUpdateAPI.as_view(), name='scene_save'),
    path('api/upload/', views.AssetUploadView.as_view(), name='asset_upload'),
    path('api/info-card/<int:card_id>/update/', views.InfoCardUpdateView.as_view(), name='infocard_update'),
    path('api/info-card/<int:card_id>/read/', views.InfoCardReadAPI.as_view(), name='infocard_read'),
    path('api/asset/<int:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),
    path('management/read-logs/', views.ReadStatusListView.as_view(), name='read_logs'),
]
