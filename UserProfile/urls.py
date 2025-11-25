from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views


app_name = 'user'
# router = DefaultRouter()



urlpatterns = [
    # path(r'api/', include(router.urls)),
    path('me/', views.MyUserMethod.as_view(), name='me'),
    path('test/', views.TestView.as_view(), name='test'),

]

urls = [

]
urlpatterns.extend([path(**url) for url in urls])