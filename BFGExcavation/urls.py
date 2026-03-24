from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import (
    DashboardView, Excavation3DView,
    FoundationCreateView, FoundationUpdateView, FoundationDeleteView,
    CSVImportView,
    ProjectListView, BridgeListView, PlanListView,
    FoundationListView, FoundationExcavationAPIView,
    FoundationStatsAPIView, HierarchyAPIView,
)

app_name = 'bfg'

urlpatterns = [
    # Web Pages
    path('', DashboardView.as_view(), name='dashboard'),
    path('3d/', Excavation3DView.as_view(), name='3d'),
    path('create/', FoundationCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', FoundationUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', FoundationDeleteView.as_view(), name='delete'),
    path('import/', CSVImportView.as_view(), name='import'),

    # REST API
    path('api/projects/', ProjectListView.as_view(), name='api-projects'),
    path('api/bridges/', BridgeListView.as_view(), name='api-bridges'),
    path('api/plans/', PlanListView.as_view(), name='api-plans'),
    path('api/foundations/', FoundationListView.as_view(), name='api-foundations'),
    path('api/stats/', FoundationStatsAPIView.as_view(), name='api-stats'),
    path('api/hierarchy/', HierarchyAPIView.as_view(), name='api-hierarchy'),
    path('api/excavation/', csrf_exempt(FoundationExcavationAPIView.as_view()), name='api-excavation'),
    path('api/excavation/<str:bridge_id>/', csrf_exempt(FoundationExcavationAPIView.as_view()), name='api-excavation-detail'),
]
