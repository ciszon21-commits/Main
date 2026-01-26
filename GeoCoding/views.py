from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.views.generic import TemplateView

from .models import GeoQuery
from .serializers import (
    GeocodeRequestSerializer, 
    GeocodeResponseSerializer,
    GeoQuerySerializer,
    SuggestionSerializer
)
from .services import get_geocoding_service


class GeocodeAPIView(APIView):
    """
    地理編碼 API
    
    POST /api/geocoding/geocode/
    將地名或地址轉換為經緯度座標
    
    支援輸入格式:
    - 完整地址: "台北市中山區中山里"
    - 部分地址: "中山區" 或 "板橋"
    - 模糊輸入: "台北中山" 
    """
    
    def post(self, request):
        serializer = GeocodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'message': '參數錯誤', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = serializer.validated_data['query']
        service = get_geocoding_service()
        result = service.geocode(query)
        
        response_serializer = GeocodeResponseSerializer(result)
        return Response(response_serializer.data)


class SuggestAPIView(APIView):
    """
    搜尋建議 API (自動完成)
    
    GET /api/geocoding/suggest/?q=台北
    """
    
    def get(self, request):
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        
        if not query:
            return Response([])
        
        service = get_geocoding_service()
        suggestions = service.search_suggestions(query, limit=limit)
        
        serializer = SuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)


class GeoQueryHistoryPagination(PageNumberPagination):
    """查詢歷史分頁設定"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class GeoQueryHistoryAPIView(ListAPIView):
    """
    查詢歷史 API
    
    GET /api/geocoding/history/
    取得最近的查詢紀錄
    """
    queryset = GeoQuery.objects.select_related(
        'matched_county', 'matched_township', 'matched_village'
    ).all()
    serializer_class = GeoQuerySerializer
    pagination_class = GeoQueryHistoryPagination


class GeocodingDashboardView(TemplateView):
    """查詢歷史儀表板"""
    template_name = 'geocoding/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_queries'] = GeoQuery.objects.select_related(
            'matched_county', 'matched_township', 'matched_village'
        ).all()[:50]
        return context


class TileCodeAPIView(APIView):
    """
    圖幅編號轉換 API
    
    POST /api/geocoding/tile/
    將圖幅編號轉換為經緯度座標，或反向轉換
    
    Request Body (圖幅 -> 座標):
        {"tile_code": "9523-III-SW"}
    
    Request Body (座標 -> 圖幅):
        {"lat": 25.0, "lng": 121.5, "scale": "1:5000"}
    
    Response:
        {
            "success": true,
            "tile_code": "9523-III-SW",
            "scale": "1:25000",
            "center": {"lat": 22.5625, "lng": 119.0625},
            "bounds": {
                "sw": {"lat": 22.5, "lng": 119.0},
                "ne": {"lat": 22.625, "lng": 119.125}
            }
        }
    """
    
    def post(self, request):
        from .tile_converter import get_tile_converter
        converter = get_tile_converter()
        
        tile_code = request.data.get('tile_code')
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        scale = request.data.get('scale', '1:5000')
        
        # 圖幅編號 -> 座標
        if tile_code:
            result = converter.parse_tile_code(tile_code)
            if result.success:
                return Response({
                    'success': True,
                    'tile_code': result.tile_code,
                    'scale': result.scale,
                    'center': {
                        'lat': result.center_lat,
                        'lng': result.center_lng
                    },
                    'bounds': {
                        'sw': {'lat': result.sw_lat, 'lng': result.sw_lng},
                        'ne': {'lat': result.ne_lat, 'lng': result.ne_lng}
                    },
                    'message': result.message
                })
            else:
                return Response({
                    'success': False,
                    'message': result.message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # 座標 -> 圖幅編號
        elif lat is not None and lng is not None:
            try:
                lat = float(lat)
                lng = float(lng)
                tile_code = converter.coordinate_to_tile(lat, lng, scale)
                result = converter.parse_tile_code(tile_code)
                return Response({
                    'success': True,
                    'tile_code': tile_code,
                    'scale': scale,
                    'center': {
                        'lat': result.center_lat if result.success else lat,
                        'lng': result.center_lng if result.success else lng
                    },
                    'bounds': {
                        'sw': {'lat': result.sw_lat, 'lng': result.sw_lng},
                        'ne': {'lat': result.ne_lat, 'lng': result.ne_lng}
                    } if result.success else None,
                    'message': '座標轉換成功'
                })
            except (ValueError, TypeError) as e:
                return Response({
                    'success': False,
                    'message': f'座標格式錯誤: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': '請提供 tile_code 或 lat/lng 座標'
        }, status=status.HTTP_400_BAD_REQUEST)

