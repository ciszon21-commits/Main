from django.urls import path
from . import views

app_name = 'codis_windrose_plotter'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_data, name='search_data'),
    path('upload/', views.upload_csv, name='upload_csv'),
]
