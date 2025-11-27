from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    path('', views.gallery_list, name='list'),
    path('upload/', views.gallery_upload, name='upload'),
    path('upload/bulk/', views.gallery_upload_bulk, name='upload_bulk'),
    path('batch-edit/', views.gallery_batch_edit, name='batch_edit'),
    path('<int:pk>/', views.gallery_detail, name='detail'),
    path('<int:pk>/rate/', views.image_rate, name='rate'),
    path('leaderboard/', views.leaderboard, name='leaderboard_all'),
    path('leaderboard/<str:period>/', views.leaderboard, name='leaderboard'),
    path('categories/', views.category_manage, name='category_manage'),
]
