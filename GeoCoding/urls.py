from django.urls import path
from .views import GeocodingDashboardView

app_name = 'geocoding'

urlpatterns = [
    path('', GeocodingDashboardView.as_view(), name='dashboard'),
]
