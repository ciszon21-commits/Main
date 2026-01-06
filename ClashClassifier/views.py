from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.middleware.csrf import get_token

from .models import ClashReport, ClassificationResult
from .serializers import (
    ClashReportSerializer,
    ClashReportListSerializer,
    ClashReportUploadSerializer,
    ClassificationResultSerializer
)
from .services import process_clash_report

def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

def redirect_view(request):
    return redirect('http://localhost:5173')

class StandardResultsSetPagination(PageNumberPagination):
    """標準分頁設定"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ClashReportViewSet(viewsets.ModelViewSet):
    """碰撞報告 ViewSet"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """只返回當前使用者的報告，排除已刪除的"""
        return ClashReport.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).prefetch_related('classifications')
    
    def get_serializer_class(self):
        """根據 action 選擇不同的 serializer"""
        if self.action == 'list':
            return ClashReportListSerializer
        elif self.action == 'create':
            return ClashReportUploadSerializer
        return ClashReportSerializer
    
    def create(self, request, *args, **kwargs):
        """
        上傳碰撞報告並自動進行分類
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 創建報告
        clash_report = serializer.save()
        
        try:
            # 處理報告：解析 HTML、生成 CSV、執行分類
            records, predictions = process_clash_report(clash_report)
            
            # 返回完整報告資訊
            output_serializer = ClashReportSerializer(clash_report)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            # 如果處理失敗，刪除報告
            clash_report.delete()
            return Response(
                {'error': f'處理報告時發生錯誤: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """軟刪除報告"""
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def classifications(self, request, pk=None):
        """取得特定報告的所有分類結果（支援分頁）"""
        clash_report = self.get_object()
        
        # 取得查詢參數
        predicted_class = request.query_params.get('predicted_class', None)
        status_filter = request.query_params.get('status', None)
        
        # 建立查詢
        queryset = clash_report.classifications.all()
        
        if predicted_class is not None:
            queryset = queryset.filter(predicted_class=int(predicted_class))
        
        if status_filter is not None:
            queryset = queryset.filter(status=int(status_filter))
        
        # 分頁
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ClassificationResultSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ClassificationResultSerializer(queryset, many=True)
        return Response(serializer.data)


class ClassificationResultViewSet(viewsets.ReadOnlyModelViewSet):
    """分類結果 ViewSet（只讀）"""
    serializer_class = ClassificationResultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """只返回當前使用者報告的分類結果"""
        return ClassificationResult.objects.filter(
            report__user=self.request.user,
            report__is_deleted=False
        ).select_related('report')
