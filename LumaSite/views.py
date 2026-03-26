from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import TemplateView
from .models import Project, Scenario, SceneAsset, AnalysisRun, AnalysisResult
from .serializers import (
    ProjectSerializer, ScenarioSerializer, SceneAssetSerializer, 
    AnalysisRunSerializer, AnalysisResultSerializer
)
from django.utils import timezone

from .services import SunPositionService
from rest_framework.views import APIView

class DashboardView(TemplateView):
    template_name = "lumasite/index.html"

class SunPositionView(APIView):
    """
    API 取得特定時間地點的太陽位置。
    """
    def get(self, request):
        lat = float(request.query_params.get('lat', 25.04))
        lng = float(request.query_params.get('lng', 121.51))
        date_str = request.query_params.get('date')
        time_minutes = int(request.query_params.get('minutes', 720))
        
        # 建立 datetime
        if date_str:
            dt_str = f"{date_str} {time_minutes // 60:02d}:{time_minutes % 60:02d}:00"
            dt = timezone.make_aware(timezone.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"))
        else:
            dt = timezone.now()
            
        azimuth, elevation = SunPositionService.get_sun_position(lat, lng, dt)
        return Response({
            'azimuth': azimuth,
            'elevation': elevation,
            'dt': dt.isoformat()
        })

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer

class SceneAssetViewSet(viewsets.ModelViewSet):
    queryset = SceneAsset.objects.all()
    serializer_class = SceneAssetSerializer

class AnalysisRunViewSet(viewsets.ModelViewSet):
    queryset = AnalysisRun.objects.all()
    serializer_class = AnalysisRunSerializer

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """
        手動觸發日照分析任務。
        """
        analysis_run = self.get_object()
        if analysis_run.status == 'running':
            return Response({'status': 'Already running'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新狀態為執行中
        analysis_run.status = 'running'
        analysis_run.started_at = timezone.now()
        analysis_run.save()
        
        # TODO: 這裡之後會串接背景任務 (Celery/RQ) 執行實際計算
        # 目前先模擬開始執行
        return Response({'status': 'Analysis triggered', 'id': analysis_run.id})

class AnalysisResultViewSet(viewsets.ModelViewSet):
    queryset = AnalysisResult.objects.all()
    serializer_class = AnalysisResultSerializer
