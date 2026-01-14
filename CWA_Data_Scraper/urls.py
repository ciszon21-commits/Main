from django.urls import path
from . import views

app_name = 'cwa_data_scraper'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_data, name='search_data'),
]
