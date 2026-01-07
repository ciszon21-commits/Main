from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from ClashClassifier.models import MLModel, ClashReport, ClassificationResult

class MLModelTest(TestCase):
    def setUp(self):
        self.file = SimpleUploadedFile("model.pkl", b"content")

    def test_single_active_model_per_type(self):
        """測試同一類型只能有一個啟用的模型"""
        # 創建第一個啟用的模型
        model1 = MLModel.objects.create(
            model_type='xgboost',
            file=self.file,
            is_active=True,
            description="Model 1"
        )
        
        # 創建第二個啟用的模型
        model2 = MLModel.objects.create(
            model_type='xgboost',
            file=self.file,
            is_active=True,
            description="Model 2"
        )
        
        # 驗證 model1 被設為未啟用
        model1.refresh_from_db()
        self.assertFalse(model1.is_active)
        self.assertTrue(model2.is_active)
        
        # 創建不同類型的啟用模型，不應影響 model2
        pca_model = MLModel.objects.create(
            model_type='pca',
            file=self.file,
            is_active=True,
            description="PCA Model"
        )
        
        model2.refresh_from_db()
        self.assertTrue(model2.is_active)
        self.assertTrue(pca_model.is_active)

    def test_string_representation(self):
        model = MLModel.objects.create(
            model_type='xgboost',
            file=self.file,
            is_active=True
        )
        self.assertEqual(str(model), "XGBoost 模型 - 啟用")
        
        model.is_active = False
        model.save()
        self.assertEqual(str(model), "XGBoost 模型 - 未啟用")

class ClashReportTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.html_file = SimpleUploadedFile("report.html", b"<html></html>")

    def test_create_clash_report(self):
        report = ClashReport.objects.create(
            user=self.user,
            title="Test Report",
            html_file=self.html_file
        )
        self.assertEqual(str(report), f"Test Report - {self.user.username}")
        self.assertFalse(report.is_deleted)
        self.assertIsNone(report.deleted_at)

    def test_soft_delete(self):
        report = ClashReport.objects.create(
            user=self.user,
            title="Test Report",
            html_file=self.html_file
        )
        
        report.soft_delete()
        report.refresh_from_db()
        
        self.assertTrue(report.is_deleted)
        self.assertIsNotNone(report.deleted_at)

class ClassificationResultTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.report = ClashReport.objects.create(
            user=self.user,
            title="Test Report",
            html_file=SimpleUploadedFile("report.html", b"<html></html>")
        )

    def test_create_classification_result(self):
        result = ClassificationResult.objects.create(
            report=self.report,
            row_index=1,
            distance=10.5,
            item1_id="123",
            item1_system="DR",
            item1_type="Type A",
            item1_count=5,
            item2_id="456",
            item2_system="SW",
            item2_type="Type B",
            item2_count=3,
            status=1,
            predicted_class=1,
            confidence=0.85
        )
        
        self.assertEqual(str(result), f"Report {self.report.id} - Row 1")
        self.assertEqual(result.report, self.report)
