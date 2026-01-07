from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from ClashClassifier.models import ClashReport, ClassificationResult

@override_settings(ENABLE_CLASH_CLASSIFIER=True)
class ClashReportViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.other_user = User.objects.create_user(username='otheruser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.html_file = SimpleUploadedFile("report.html", b"<html></html>", content_type="text/html")

    @patch('ClashClassifier.views.process_clash_report')
    def test_upload_report(self, mock_process):
        """測試上傳報告"""
        # 設置 mock 返回值
        mock_process.return_value = ([], []) # records, predictions
        
        data = {'html_file': self.html_file}
        url = reverse('clash-report-list')
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClashReport.objects.count(), 1)
        self.assertTrue(mock_process.called)

    def test_list_reports(self):
        """測試報告列表"""
        # 當前使用者的報告
        ClashReport.objects.create(user=self.user, title="My Report", html_file=self.html_file)
        # 其他使用者的報告
        ClashReport.objects.create(user=self.other_user, title="Other Report", html_file=self.html_file)
        # 已刪除的報告
        repo = ClashReport.objects.create(user=self.user, title="Deleted Report", html_file=self.html_file)
        repo.soft_delete()
        
        url = reverse('clash-report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 應該只看到 1 個（自己的、未刪除的）
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "My Report")

    def test_soft_delete_report(self):
        """測試軟刪除報告"""
        report = ClashReport.objects.create(user=self.user, title="Report", html_file=self.html_file)
        
        url = reverse('clash-report-detail', kwargs={'pk': report.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        report.refresh_from_db()
        self.assertTrue(report.is_deleted)

    def test_get_classifications(self):
        """測試取得報告的所有分類"""
        report = ClashReport.objects.create(user=self.user, title="Report", html_file=self.html_file)
        ClassificationResult.objects.create(
            report=report, row_index=1, distance=10, 
            item1_id="1", item1_system="A", item1_type="T", item1_count=1,
            item2_id="2", item2_system="B", item2_type="T", item2_count=1,
            predicted_class=1, confidence=0.9
        )
        
        # Action URL needs to be constructed or reversed carefully. 
        # Standard router reversal for @action: basename-action_name
        url = reverse('clash-report-classifications', kwargs={'pk': report.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

@override_settings(ENABLE_CLASH_CLASSIFIER=True)
class ClassificationResultViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.report = ClashReport.objects.create(
            user=self.user, 
            title="Report", 
            html_file=SimpleUploadedFile("report.html", b"<html></html>")
        )

    def test_list_results(self):
        """測試列出分類結果"""
        ClassificationResult.objects.create(
            report=self.report, row_index=1, distance=10, 
            item1_id="1", item1_system="A", item1_type="T", item1_count=1,
            item2_id="2", item2_system="B", item2_type="T", item2_count=1,
            predicted_class=1, confidence=0.9
        )
        
        url = reverse('classification-result-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
