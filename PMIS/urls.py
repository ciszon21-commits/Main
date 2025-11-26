from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'PMIS'
router = DefaultRouter()
# router.register(r'element', views.BElementViewSet, basename='element')

urlpatterns = [
    path(r'api/', include(router.urls)),
    path('index/', views.Index.as_view(), name='index'),

    path('vproject/', views.VProject.as_view(), name='vproject'),

]
