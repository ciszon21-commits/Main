from django.urls import path
from . import views

app_name = 'volume_calc'

urlpatterns = [
    path('', views.CalcPageView.as_view(), name='index'),
]
