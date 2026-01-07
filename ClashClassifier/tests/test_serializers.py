from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from ClashClassifier.serializers import (
    ClashReportUploadSerializer,
    ClashReportSerializer,
    ClashReportListSerializer,
    ClassificationResultSerializer
)
from ClashClassifier.models import ClashReport, ClassificationResult

class SerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.factory = APIRequestFactory()

    def test_upload_serializer_valid_file(self):
        """測試上傳合法的 HTML 檔案"""
        file = SimpleUploadedFile("test.html", b"<html></html>", content_type="text/html")
        data = {'html_file': file}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = ClashReportUploadSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        report = serializer.save()
        self.assertEqual(report.title, "test")  # 自動使用檔名當標題
        self.assertEqual(report.user, self.user)

    def test_upload_serializer_invalid_extension(self):
        """測試上傳非 HTML 檔案"""
        file = SimpleUploadedFile("test.txt", b"text content", content_type="text/plain")
        data = {'html_file': file}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = ClashReportUploadSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('html_file', serializer.errors)

    def test_clash_report_serializer_fields(self):
        """測試 ClashReportSerializer 的欄位輸出"""
        report = ClashReport.objects.create(
            user=self.user,
            title="Detailed Report",
            html_file=SimpleUploadedFile("report.html", b"<html></html>")
        )
        
        # 創建一些分類結果
        ClassificationResult.objects.create(
            report=report, row_index=1, distance=5.0,
            item1_id="1", item1_system="A", item1_type="T1", item1_count=1,
            item2_id="2", item2_system="B", item2_type="T2", item2_count=1,
            predicted_class=1, confidence=0.9
        )
        ClassificationResult.objects.create(
            report=report, row_index=2, distance=10.0,
            item1_id="3", item1_system="A", item1_type="T1", item1_count=1,
            item2_id="4", item2_system="B", item2_type="T2", item2_count=1,
            predicted_class=0, confidence=0.8
        )
        
        serializer = ClashReportSerializer(report)
        data = serializer.data
        
        self.assertEqual(data['title'], "Detailed Report")
        self.assertEqual(data['classification_count'], 2)
        self.assertEqual(data['clash_count'], 1)
        self.assertEqual(len(data['classifications']), 2)

    def test_classification_result_serializer(self):
        """測試 ClassificationResultSerializer"""
        report = ClashReport.objects.create(
            user=self.user,
            title="Report",
            html_file=SimpleUploadedFile("report.html", b"<html></html>")
        )
        result = ClassificationResult.objects.create(
            report=report, row_index=1, distance=5.0,
            item1_id="1", item1_system="A", item1_type="T1", item1_count=1,
            item2_id="2", item2_system="B", item2_type="T2", item2_count=1,
            status=1,  # 作用中
            predicted_class=1, # 是碰撞
            confidence=0.9
        )
        
        serializer = ClassificationResultSerializer(result)
        data = serializer.data
        
        self.assertEqual(data['status_display'], '作用中')
        self.assertEqual(data['predicted_class_display'], '是碰撞')
        self.assertEqual(data['distance'], 5.0)
