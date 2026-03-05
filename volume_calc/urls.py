from django.urls import path
from .views import CalculatorView

app_name = 'volume_calc'

urlpatterns = [
    path('', CalculatorView.as_view(), name='calculator'),
]
