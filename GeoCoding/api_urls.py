from django.urls import path
from .views import GeocodeAPIView, GeoQueryHistoryAPIView, SuggestAPIView, TileCodeAPIView

urlpatterns = [
    path('geocode/', GeocodeAPIView.as_view(), name='geocode'),
    path('history/', GeoQueryHistoryAPIView.as_view(), name='history'),
    path('suggest/', SuggestAPIView.as_view(), name='suggest'),
    path('tile/', TileCodeAPIView.as_view(), name='tile'),
]

