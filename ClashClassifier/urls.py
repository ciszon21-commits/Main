from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ClashReportViewSet, ClassificationResultViewSet

router = DefaultRouter()
router.register(r'reports', ClashReportViewSet, basename='clash-report')
router.register(r'classifications', ClassificationResultViewSet, basename='classification-result')

urlpatterns = [
    path('', include(router.urls)),
    path('get_csrf_token/', views.get_csrf_token, name="get_csrf_token"),
    path('redirect/', views.redirect_view, name='redirect')
]
