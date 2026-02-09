"""
Views for Circle Optimizer App
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from .models import Shape, CircleConfig, Circle
from .serializers import (
    ShapeSerializer, CircleConfigSerializer, CircleSerializer,
    OptimizeRequestSerializer, AdjustCircleSerializer
)
from .optimizer import optimize_3_circles, optimize_4_circles, calculate_arc_params


def home(request):
    """首頁視圖"""
    return render(request, 'CircleOptimizer/home.html')


class ShapeViewSet(viewsets.ModelViewSet):
    """Shape API ViewSet"""
    queryset = Shape.objects.all()
    serializer_class = ShapeSerializer
    
    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """
        執行圓優化
        POST /api/shapes/{id}/optimize/
        Body: {"config_type": "3_circle" or "4_circle"}
        """
        shape = self.get_object()
        serializer = OptimizeRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config_type = serializer.validated_data['config_type']
        points = shape.points
        
        # 執行優化
        try:
            if config_type == '3_circle':
                result = optimize_3_circles(points)
            else:
                result = optimize_4_circles(points)
            
            if not result['success']:
                return Response(
                    {'error': '優化失敗', 'message': result.get('message', '')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 創建 CircleConfig
            config = CircleConfig.objects.create(
                shape=shape,
                config_type=config_type,
                total_area=result['total_area'],
                is_optimized=True
            )
            
            # 創建 Circle 實例
            for circle_data in result['circles']:
                Circle.objects.create(
                    config=config,
                    circle_index=circle_data['circle_index'],
                    center_x=circle_data['center_x'],
                    center_y=circle_data['center_y'],
                    radius=circle_data['radius'],
                    arc_length=circle_data['arc_length'],
                    start_angle=circle_data['start_angle'],
                    end_angle=circle_data['end_angle']
                )
            
            # 返回結果
            config_serializer = CircleConfigSerializer(config)
            return Response(config_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': '優化過程發生錯誤', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def calculate_tangent(self, request, pk=None):
        """
        計算與兩個圓相切的第三個圓（互動模式）
        POST /api/shapes/{id}/calculate_tangent/
        Body: {
            "circle1": {"center_x": 0, "center_y": 0, "radius": 10},
            "circle2": {"center_x": 20, "center_y": 0, "radius": 10}
        }
        """
        shape = self.get_object()
        
        try:
            c1 = request.data.get('circle1', {})
            c2 = request.data.get('circle2', {})
            
            if not c1 or not c2:
                return Response(
                    {'error': '缺少圓的參數'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from .tangent_solver import optimize_4_circles_interactive
            
            # 提取角度參數（如果存在）
            c1_angles = None
            if 'start_angle' in c1 and 'end_angle' in c1:
                c1_angles = (float(c1['start_angle']), float(c1['end_angle']))
                
            c2_angles = None
            if 'start_angle' in c2 and 'end_angle' in c2:
                c2_angles = (float(c2['start_angle']), float(c2['end_angle']))
            
            result = optimize_4_circles_interactive(
                float(c1['center_x']),
                float(c1['center_y']),
                float(c1['radius']),
                float(c2['center_x']),
                float(c2['center_y']),
                float(c2['radius']),
                shape.points,
                c1_angles=c1_angles,
                c2_angles=c2_angles
            )
            
            if not result['success']:
                return Response(
                    {'error': '計算失敗', 'message': result.get('message', '')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 不儲存到資料庫，只返回計算結果供即時預覽
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': '計算過程發生錯誤', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CircleConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """Circle Configuration API ViewSet (Read Only)"""
    queryset = CircleConfig.objects.all()
    serializer_class = CircleConfigSerializer
    
    @action(detail=True, methods=['put', 'patch'])
    def adjust(self, request, pk=None):
        """
        手動調整圓參數
        PUT/PATCH /api/configs/{id}/adjust/
        Body: {"circles": [{"circle_index": 0, "center_x": 10, "center_y": 20, "radius": 5}, ...]}
        """
        config = self.get_object()
        serializer = AdjustCircleSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        circles_data = serializer.validated_data['circles']
        
        try:
            # 更新圓參數
            for circle_data in circles_data:
                circle_index = circle_data['circle_index']
                
                try:
                    circle = Circle.objects.get(
                        config=config,
                        circle_index=circle_index
                    )
                except Circle.DoesNotExist:
                    return Response(
                        {'error': f'圓索引 {circle_index} 不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # 更新基本參數
                circle.center_x = float(circle_data['center_x'])
                circle.center_y = float(circle_data['center_y'])
                circle.radius = float(circle_data['radius'])
                
                # 重新計算弧長和角度
                arc_data = calculate_arc_params(
                    circle.center_x,
                    circle.center_y,
                    circle.radius,
                    config.shape.points
                )
                circle.arc_length = arc_data['arc_length']
                circle.start_angle = arc_data['start_angle']
                circle.end_angle = arc_data['end_angle']
                
                circle.save()
            
            # 重新計算總面積
            total_area = 0
            for circle in config.circles.all():
                import math
                total_area += math.pi * circle.radius**2
            
            config.total_area = total_area
            config.is_optimized = False  # 標記為手動調整
            config.save()
            
            # 返回更新後的配置
            config_serializer = CircleConfigSerializer(config)
            return Response(config_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': '調整參數時發生錯誤', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CircleViewSet(viewsets.ReadOnlyModelViewSet):
    """Circle API ViewSet (Read Only)"""
    queryset = Circle.objects.all()
    serializer_class = CircleSerializer
