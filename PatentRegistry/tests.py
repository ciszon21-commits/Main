from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from PatentRegistry.models import (
    PatentApplication, PatentRebuttal, GrantedPatent, PatentAnnuity,
    PatentAdmin
)


class PatentApplicationModelTest(TestCase):
    """測試專利申請模型"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.application = PatentApplication.objects.create(
            plan_number='PLAN-001',
            outsource_number='OUT-001',
            item_number=1,
            name='測試專利',
            category='INVENTION',
            patent_firm='測試事務所',
            firm_case_number='CASE-001',
            created_by=self.user
        )
    
    def test_application_creation(self):
        """測試專利申請建立"""
        self.assertEqual(self.application.name, '測試專利')
        self.assertEqual(self.application.status, 'PENDING')
        self.assertTrue(self.application.is_pending)
        self.assertFalse(self.application.is_approved)
    
    def test_application_str(self):
        """測試字串呈現"""
        self.assertEqual(str(self.application), 'PLAN-001 - 測試專利')
    
    def test_rebuttal_count(self):
        """測試答辯次數計算"""
        self.assertEqual(self.application.rebuttal_count, 0)
        
        PatentRebuttal.objects.create(
            application=self.application,
            rebuttal_type='FIRST',
            document_date=date.today(),
            fee=Decimal('1000.00')
        )
        
        self.assertEqual(self.application.rebuttal_count, 1)
    
    def test_total_rebuttal_fee(self):
        """測試答辯費用總計"""
        PatentRebuttal.objects.create(
            application=self.application,
            rebuttal_type='FIRST',
            document_date=date.today(),
            fee=Decimal('1000.00')
        )
        PatentRebuttal.objects.create(
            application=self.application,
            rebuttal_type='SECOND',
            document_date=date.today(),
            fee=Decimal('2000.00')
        )
        
        self.assertEqual(self.application.total_rebuttal_fee, Decimal('3000.00'))


class PatentRebuttalModelTest(TestCase):
    """測試答辯記錄模型"""
    
    def setUp(self):
        self.application = PatentApplication.objects.create(
            plan_number='PLAN-001',
            name='測試專利',
            category='INVENTION',
            patent_firm='測試事務所'
        )
        self.rebuttal = PatentRebuttal.objects.create(
            application=self.application,
            rebuttal_type='FIRST',
            document_date=date.today(),
            fee=Decimal('5000.00'),
            notes='測試備註'
        )
    
    def test_rebuttal_creation(self):
        """測試答辯記錄建立"""
        self.assertEqual(self.rebuttal.fee, Decimal('5000.00'))
        self.assertEqual(self.rebuttal.rebuttal_type, 'FIRST')
    
    def test_rebuttal_str(self):
        """測試字串呈現"""
        self.assertIn('初次答辯', str(self.rebuttal))


class GrantedPatentModelTest(TestCase):
    """測試已取得專利模型"""
    
    def setUp(self):
        self.application = PatentApplication.objects.create(
            plan_number='PLAN-001',
            name='測試專利',
            category='INVENTION',
            patent_firm='測試事務所',
            status='APPROVED'
        )
        self.granted = GrantedPatent.objects.create(
            application=self.application,
            patent_number='PAT-001',
            patent_name='測試專利名稱',
            patent_period='20年',
            description='專利描述',
            start_date=date(2024, 1, 1),
            end_date=date(2044, 1, 1)
        )
    
    def test_granted_creation(self):
        """測試已取得專利建立"""
        self.assertEqual(self.granted.patent_number, 'PAT-001')
        self.assertEqual(self.granted.granted_year, 2024)
    
    def test_granted_str(self):
        """測試字串呈現"""
        self.assertEqual(str(self.granted), 'PAT-001 - 測試專利名稱')


class PatentAnnuityModelTest(TestCase):
    """測試專利年費核銷模型"""
    
    def setUp(self):
        self.application = PatentApplication.objects.create(
            plan_number='PLAN-001',
            name='測試專利',
            category='INVENTION',
            patent_firm='測試事務所',
            status='APPROVED'
        )
        self.granted = GrantedPatent.objects.create(
            application=self.application,
            patent_number='PAT-001',
            patent_name='測試專利名稱',
            start_date=date(2024, 1, 1),
            end_date=date(2044, 1, 1)
        )
        self.annuity = PatentAnnuity.objects.create(
            granted_patent=self.granted,
            write_off_plan_number='WO-001',
            write_off_date=date(2025, 1, 1),
            year=2025,
            notes='年費核銷備註'
        )
    
    def test_annuity_creation(self):
        """測試年費核銷建立"""
        self.assertEqual(self.annuity.year, 2025)
        self.assertEqual(self.annuity.write_off_plan_number, 'WO-001')
    
    def test_annuity_str(self):
        """測試字串呈現"""
        self.assertIn('2025', str(self.annuity))


class PatentViewsTest(TestCase):
    """測試專利視圖"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.application = PatentApplication.objects.create(
            plan_number='PLAN-001',
            name='測試專利',
            category='INVENTION',
            patent_firm='測試事務所',
            created_by=self.user
        )
        # 賦予專利管理員權限
        PatentAdmin.objects.create(user=self.user, created_by=self.user)
    
    def test_public_list_view(self):
        """測試公開首頁"""
        response = self.client.get(reverse('patent_registry:public_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'patent_registry/public_patent_list.html')
    
    def test_application_list_requires_login(self):
        """測試申請列表需要登入"""
        response = self.client.get(reverse('patent_registry:application_list'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("patent_registry:application_list")}', fetch_redirect_response=False)
    
    def test_application_list_logged_in(self):
        """測試登入後可訪問申請列表"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('patent_registry:application_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_application_create_view(self):
        """測試建立申請視圖"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('patent_registry:application_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_application_detail_view(self):
        """測試申請詳情視圖"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(
            reverse('patent_registry:application_detail', kwargs={'pk': self.application.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_application_create_post(self):
        """測試提交新申請"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('patent_registry:application_create'), {
            'plan_number': 'PLAN-002',
            'outsource_number': 'OUT-002',
            'item_number': 1,
            'name': '新專利申請',
            'category': 'UTILITY_MODEL',
            'patent_firm': '新事務所',
            'firm_case_number': 'CASE-002',
        })
        self.assertRedirects(response, reverse('patent_registry:application_list'))
        self.assertTrue(PatentApplication.objects.filter(plan_number='PLAN-002').exists())
