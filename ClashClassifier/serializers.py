from rest_framework import serializers
from .models import ClashReport, ClassificationResult
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """使用者序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class ClassificationResultSerializer(serializers.ModelSerializer):
    """分類結果序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    predicted_class_display = serializers.CharField(source='get_predicted_class_display', read_only=True)
    
    class Meta:
        model = ClassificationResult
        fields = [
            'id', 'row_index', 'distance',
            'item1_id', 'item1_system', 'item1_type', 'item1_count',
            'item2_id', 'item2_system', 'item2_type', 'item2_count',
            'status', 'status_display',
            'predicted_class', 'predicted_class_display',
            'confidence', 'created_at'
        ]


class ClashReportListSerializer(serializers.ModelSerializer):
    """報告列表序列化器（簡化版）"""
    user = UserSerializer(read_only=True)
    classification_count = serializers.SerializerMethodField()
    clash_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ClashReport
        fields = [
            'id', 'title', 'user', 'uploaded_at',
            'classification_count', 'clash_count'
        ]
    
    def get_classification_count(self, obj):
        """取得分類結果總數"""
        return obj.classifications.count()
    
    def get_clash_count(self, obj):
        """取得預測為碰撞的數量"""
        return obj.classifications.filter(predicted_class=1).count()


class ClashReportSerializer(serializers.ModelSerializer):
    """完整報告序列化器"""
    user = UserSerializer(read_only=True)
    classifications = ClassificationResultSerializer(many=True, read_only=True)
    classification_count = serializers.SerializerMethodField()
    clash_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ClashReport
        fields = [
            'id', 'title', 'user', 'html_file', 'csv_file',
            'uploaded_at', 'classifications',
            'classification_count', 'clash_count'
        ]
    
    def get_classification_count(self, obj):
        """取得分類結果總數"""
        return obj.classifications.count()
    
    def get_clash_count(self, obj):
        """取得預測為碰撞的數量"""
        return obj.classifications.filter(predicted_class=1).count()


class ClashReportUploadSerializer(serializers.ModelSerializer):
    """上傳報告序列化器"""
    html_file = serializers.FileField()
    title = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = ClashReport
        fields = ['html_file', 'title']
    
    def validate_html_file(self, value):
        """驗證 HTML 檔案"""
        if not value.name.endswith('.html'):
            raise serializers.ValidationError('只接受 .html 檔案')
        
        # 檢查檔案大小 (最大 100MB)
        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError('檔案大小不能超過 100MB')
        
        return value
    
    def create(self, validated_data):
        """創建報告時自動設定使用者和標題"""
        request = self.context.get('request')
        
        # 如果沒有提供標題，使用檔案名稱
        if not validated_data.get('title'):
            validated_data['title'] = validated_data['html_file'].name.replace('.html', '')
        
        validated_data['user'] = request.user
        return super().create(validated_data)
