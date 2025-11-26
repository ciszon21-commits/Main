from django.urls import path
from . import views

app_name = 'archive'

urlpatterns = [
    path('index/', views.IndexView.as_view(), name='index'),
    path('include/', views.IncludeView.as_view(), name='include'),
    path('model/function/', views.SAFunctionView.as_view(), name='model_function'),
]
