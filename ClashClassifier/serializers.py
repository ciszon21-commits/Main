from rest_framework import serializers
from .models import ClashReport, ClassificationResult
from django.contrib.auth.models import User
from django.db.models import Count
from itertools import chain
from collections import Counter


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
    frequently_clashed_item_id = serializers.SerializerMethodField()
    
    class Meta:
        model = ClashReport
        fields = [
            'id', 'title', 'user', 'uploaded_at',
            'classification_count', 'clash_count',
            'frequently_clashed_item_id'
        ]
    
    def get_classification_count(self, obj):
        """取得分類結果總數"""
        return obj.classifications.count()
    
    def get_clash_count(self, obj):
        """取得預測為碰撞的數量"""
        return obj.classifications.filter(predicted_class=1).count()

    def get_frequently_clashed_item_id(self, obj):
        """item1_id 與 item2_id 一起比出現次數，回傳最多次的 ID"""

        qs = obj.classifications.filter(predicted_class=1)

        # 取得兩欄的計數
        item1_counts = qs.values('item1_id').annotate(c=Count('item1_id'))
        item2_counts = qs.values('item2_id').annotate(c=Count('item2_id'))

        counter = Counter()

        for row in chain(item1_counts, item2_counts):
            # row 可能是 {'item1_id': 123, 'c': 5}
            item_id = row.get('item1_id') or row.get('item2_id')
            counter[item_id] += row['c']

        if not counter:
            return None

        # 取出出現最多次的
        return counter.most_common(1)[0][0]

class ClashReportSerializer(serializers.ModelSerializer):
    """完整報告序列化器"""
    user = UserSerializer(read_only=True)
    classifications = ClassificationResultSerializer(many=True, read_only=True)
    classification_count = serializers.SerializerMethodField()
    clash_count = serializers.SerializerMethodField()
    frequently_clashed_item_id = serializers.SerializerMethodField()
    clash_matrix = serializers.SerializerMethodField()
    
    class Meta:
        model = ClashReport
        fields = [
            'id', 'title', 'user', 'html_file', 'csv_file',
            'uploaded_at', 'classifications',
            'classification_count', 'clash_count',
            'frequently_clashed_item_id', 'clash_matrix'
        ]
    
    def get_classification_count(self, obj):
        """取得分類結果總數"""
        return obj.classifications.count()

    def get_clash_count(self, obj):
        """取得預測為碰撞的數量"""
        return obj.classifications.filter(predicted_class=1).count()

    def get_frequently_clashed_item_id(self, obj):
        """item1_id 與 item2_id 一起比出現次數，回傳最多次的 ID"""

        qs = obj.classifications.filter(predicted_class=1)

        # 取得兩欄的計數
        item1_counts = qs.values('item1_id').annotate(c=Count('item1_id'))
        item2_counts = qs.values('item2_id').annotate(c=Count('item2_id'))

        counter = Counter()

        for row in chain(item1_counts, item2_counts):
            # row 可能是 {'item1_id': 123, 'c': 5}
            item_id = row.get('item1_id') or row.get('item2_id')
            counter[item_id] += row['c']

        if not counter:
            return None

        # 取出出現最多次的
        return counter.most_common(1)[0][0]
    
    def get_clash_matrix(self, obj):
        """整理碰撞矩陣 - 所有碰撞集中到右上三角（包含對角線）"""
        item1_systems = obj.classifications.values_list('item1_system', flat=True).distinct()
        item2_systems = obj.classifications.values_list('item2_system', flat=True).distinct()
        systems = sorted(set(item1_systems).union(set(item2_systems)))

        qs = obj.classifications.filter(predicted_class=1)
        matrix = {}
        
        for i, sys1 in enumerate(systems):
            matrix[sys1] = {}
            for j, sys2 in enumerate(systems):
                if i < j:
                    # 右上三角（不含對角線）：合併雙向碰撞
                    # sys1 vs sys2 的碰撞 + sys2 vs sys1 的碰撞
                    count = qs.filter(
                        item1_system=sys1, 
                        item2_system=sys2
                    ).count() + qs.filter(
                        item1_system=sys2, 
                        item2_system=sys1
                    ).count()
                    matrix[sys1][sys2] = count
                elif i == j:
                    # 對角線：只計算同系統內的碰撞
                    count = qs.filter(
                        item1_system=sys1, 
                        item2_system=sys2
                    ).count()
                    matrix[sys1][sys2] = count
                else:
                    # 左下三角：設為 null
                    matrix[sys1][sys2] = None
        
        return matrix     

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
