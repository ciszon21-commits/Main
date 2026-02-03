"""
DRF Serializers for Circle Optimizer App
"""
from rest_framework import serializers
from .models import Shape, CircleConfig, Circle


class CircleSerializer(serializers.ModelSerializer):
    """Circle serializer"""
    
    class Meta:
        model = Circle
        fields = [
            'id', 'circle_index', 'center_x', 'center_y',
            'radius', 'arc_length', 'start_angle', 'end_angle'
        ]
        read_only_fields = ['id']


class CircleConfigSerializer(serializers.ModelSerializer):
    """Circle configuration serializer with nested circles"""
    circles = CircleSerializer(many=True, read_only=True)
    config_type_display = serializers.CharField(source='get_config_type_display', read_only=True)
    
    class Meta:
        model = CircleConfig
        fields = [
            'id', 'shape', 'config_type', 'config_type_display',
            'total_area', 'is_optimized', 'circles',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShapeSerializer(serializers.ModelSerializer):
    """Shape serializer"""
    configs = CircleConfigSerializer(many=True, read_only=True)
    points_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Shape
        fields = [
            'id', 'name', 'points', 'points_count', 'configs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_points(self, value):
        """驗證控制點數據"""
        if not isinstance(value, list):
            raise serializers.ValidationError("控制點必須是陣列格式")
        
        if len(value) != 8:
            raise serializers.ValidationError("必須提供8個控制點")
        
        for i, point in enumerate(value):
            if not isinstance(point, list) or len(point) != 2:
                raise serializers.ValidationError(f"第{i+1}個點格式錯誤，應為 [x, y]")
            
            try:
                float(point[0])
                float(point[1])
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"第{i+1}個點的座標必須是數字")
        
        return value


class OptimizeRequestSerializer(serializers.Serializer):
    """優化請求serializer"""
    config_type = serializers.ChoiceField(
        choices=['3_circle', '4_circle'],
        required=True,
        help_text="選擇3心圓或4心圓"
    )


class AdjustCircleSerializer(serializers.Serializer):
    """調整圓參數的serializer"""
    circles = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="圓的參數列表"
    )
    
    def validate_circles(self, value):
        """驗證圓的參數"""
        for circle_data in value:
            required_fields = ['circle_index', 'center_x', 'center_y', 'radius']
            for field in required_fields:
                if field not in circle_data:
                    raise serializers.ValidationError(f"缺少必要欄位: {field}")
            
            try:
                float(circle_data['center_x'])
                float(circle_data['center_y'])
                float(circle_data['radius'])
                int(circle_data['circle_index'])
            except (ValueError, TypeError):
                raise serializers.ValidationError("參數類型錯誤")
            
            if float(circle_data['radius']) <= 0:
                raise serializers.ValidationError("半徑必須大於0")
        
        return value
