from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardView, SunPositionView,
    ProjectViewSet, ScenarioViewSet, SceneAssetViewSet, 
    AnalysisRunViewSet, AnalysisResultViewSet
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'scenarios', ScenarioViewSet)
router.register(r'assets', SceneAssetViewSet)
router.register(r'analysis-runs', AnalysisRunViewSet)
router.register(r'analysis-results', AnalysisResultViewSet)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('sun-position/', SunPositionView.as_view(), name='sun-position'),
    path('api/', include(router.urls)),
]
