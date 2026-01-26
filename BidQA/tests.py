from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
import io

from .models import Bid, Committee, BidCommittee, Question, BidFile, FileDownloadLog
from .forms import BidForm, CommitteeForm, QuestionForm, CommitteeSelectForm, BidFileForm


class BidModelTestCase(TestCase):
    """標案模型測試"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bid = Bid.objects.create(
            name='測試標案A',
            bid_number='TEST-001',
            bid_date=date.today(),
            status='won',
            description='測試說明',
            created_by=self.user
        )
    
    def test_bid_creation(self):
        """測試標案建立"""
        self.assertEqual(self.bid.name, '測試標案A')
        self.assertEqual(self.bid.status, 'won')
        self.assertEqual(str(self.bid), '測試標案A')
    
    def test_bid_committee_count(self):
        """測試委員數量計算"""
        committee1 = Committee.objects.create(name='委員甲', organization='單位A')
        committee2 = Committee.objects.create(name='委員乙', organization='單位B')
        BidCommittee.objects.create(bid=self.bid, committee=committee1)
        BidCommittee.objects.create(bid=self.bid, committee=committee2)
        
        self.assertEqual(self.bid.get_committee_count(), 2)
    
    def test_bid_question_count(self):
        """測試問答數量計算"""
        committee = Committee.objects.create(name='委員甲', organization='單位A')
        bc = BidCommittee.objects.create(bid=self.bid, committee=committee)
        Question.objects.create(bid_committee=bc, question='問題1', answer='答案1')
        Question.objects.create(bid_committee=bc, question='問題2', answer='答案2')
        
        self.assertEqual(self.bid.get_question_count(), 2)


class CommitteeModelTestCase(TestCase):
    """委員模型測試"""
    
    def setUp(self):
        self.committee = Committee.objects.create(
            name='王委員',
            organization='台灣大學',
            specialty='環境工程'
        )
    
    def test_committee_creation(self):
        """測試委員建立"""
        self.assertEqual(self.committee.name, '王委員')
        self.assertEqual(str(self.committee), '王委員 (台灣大學)')
    
    def test_committee_without_organization(self):
        """測試無單位的委員"""
        committee = Committee.objects.create(name='李委員')
        self.assertEqual(str(committee), '李委員')
    
    def test_committee_question_count(self):
        """測試委員問答數量"""
        user = User.objects.create_user(username='test', password='pass')
        bid = Bid.objects.create(name='標案', created_by=user)
        bc = BidCommittee.objects.create(bid=bid, committee=self.committee)
        Question.objects.create(bid_committee=bc, question='Q1', answer='A1')
        
        self.assertEqual(self.committee.get_question_count(), 1)


class BidFileModelTestCase(TestCase):
    """檔案模型測試"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bid = Bid.objects.create(name='測試標案', created_by=self.user)
        self.bid_file = BidFile.objects.create(
            bid=self.bid,
            file='test.pdf',
            filename='測試文件.pdf',
            uploaded_by=self.user
        )
    
    def test_file_creation(self):
        """測試檔案建立"""
        self.assertEqual(self.bid_file.filename, '測試文件.pdf')
        self.assertEqual(str(self.bid_file), '測試文件.pdf')
    
    def test_download_count(self):
        """測試下載次數"""
        FileDownloadLog.objects.create(
            file=self.bid_file,
            downloaded_by=self.user,
            ip_address='127.0.0.1'
        )
        FileDownloadLog.objects.create(
            file=self.bid_file,
            downloaded_by=self.user,
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(self.bid_file.get_download_count(), 2)


class BidViewTestCase(TestCase):
    """標案 Views 測試"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.bid = Bid.objects.create(
            name='測試標案',
            bid_number='TEST-001',
            created_by=self.user
        )
    
    def test_bid_list_view(self):
        """測試標案列表"""
        response = self.client.get(reverse('bidqa:bid_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試標案')
    
    def test_bid_detail_view(self):
        """測試標案詳情"""
        response = self.client.get(reverse('bidqa:bid_detail', args=[self.bid.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試標案')
    
    def test_bid_create_view(self):
        """測試建立標案"""
        response = self.client.post(reverse('bidqa:bid_create'), {
            'name': '新標案',
            'bid_number': 'NEW-001',
            'bid_date': date.today(),
            'status': 'won',
            'description': '新標案說明'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Bid.objects.filter(name='新標案').exists())
    
    def test_bid_update_view(self):
        """測試更新標案"""
        response = self.client.post(reverse('bidqa:bid_update', args=[self.bid.pk]), {
            'name': '更新後標案',
            'bid_number': 'TEST-001',
            'status': 'won'
        })
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.name, '更新後標案')
    
    def test_bid_delete_view(self):
        """測試刪除標案"""
        response = self.client.post(reverse('bidqa:bid_delete', args=[self.bid.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Bid.objects.filter(pk=self.bid.pk).exists())


class CommitteeViewTestCase(TestCase):
    """委員 Views 測試"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.committee = Committee.objects.create(
            name='王委員',
            organization='台灣大學'
        )
    
    def test_committee_list_view(self):
        """測試委員列表"""
        response = self.client.get(reverse('bidqa:committee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '王委員')
    
    def test_committee_detail_view(self):
        """測試委員詳情"""
        response = self.client.get(reverse('bidqa:committee_detail', args=[self.committee.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '王委員')
    
    def test_committee_create_view(self):
        """測試建立委員"""
        response = self.client.post(reverse('bidqa:committee_create'), {
            'name': '李委員',
            'organization': '清華大學',
            'specialty': '資訊工程'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Committee.objects.filter(name='李委員').exists())


class FileUploadTestCase(TestCase):
    """檔案上傳測試"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.bid = Bid.objects.create(name='測試標案', created_by=self.user)
    
    def test_file_upload_view(self):
        """測試檔案上傳"""
        # 建立測試檔案
        test_file = SimpleUploadedFile(
            "test_document.txt",
            b"This is test content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('bidqa:file_upload', args=[self.bid.pk]),
            {'file': test_file, 'description': '測試文件'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BidFile.objects.filter(bid=self.bid).exists())
    
    def test_file_download_logging(self):
        """測試下載記錄"""
        bid_file = BidFile.objects.create(
            bid=self.bid,
            file='test.txt',
            filename='test.txt',
            uploaded_by=self.user
        )
        
        # 模擬下載
        response = self.client.get(reverse('bidqa:file_download', args=[bid_file.pk]))
        
        # 檢查下載記錄是否建立
        self.assertTrue(FileDownloadLog.objects.filter(file=bid_file).exists())


class QuickSearchTestCase(TestCase):
    """快速搜尋測試"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # 建立測試資料
        self.committee = Committee.objects.create(name='王委員', organization='台灣大學')
        self.bid = Bid.objects.create(name='測試標案', created_by=self.user)
        self.bc = BidCommittee.objects.create(bid=self.bid, committee=self.committee)
        Question.objects.create(
            bid_committee=self.bc,
            question='關於水庫的問題',
            answer='水庫相關答案'
        )
    
    def test_search_by_committee_name(self):
        """測試委員姓名搜尋"""
        response = self.client.get(reverse('bidqa:quick_search') + '?q=王委員')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '王委員')
    
    def test_search_by_question_content(self):
        """測試問題內容搜尋"""
        response = self.client.get(reverse('bidqa:quick_search') + '?q=水庫')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '水庫')


class APITestCase(TestCase):
    """API 測試"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        Committee.objects.create(name='王委員', organization='台灣大學')
        Committee.objects.create(name='王建民', organization='清華大學')
    
    def test_search_committees_by_name_api(self):
        """測試姓名搜尋 API"""
        response = self.client.get(
            reverse('bidqa:search_committees_by_name_api') + '?name=王'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['committees']), 0)
        self.assertTrue(any('王' in c['name'] for c in data['committees']))


class FormTestCase(TestCase):
    """表單測試"""
    
    def test_bid_form_valid(self):
        """測試標案表單驗證"""
        form_data = {
            'name': '測試標案',
            'bid_number': 'TEST-001',
            'bid_date': date.today(),
            'status': 'won',
            'description': '說明'
        }
        form = BidForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_committee_form_valid(self):
        """測試委員表單驗證"""
        form_data = {
            'name': '王委員',
            'organization': '台灣大學',
            'specialty': '環境工程'
        }
        form = CommitteeForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_committee_select_form_validation(self):
        """測試委員選擇表單驗證"""
        # 測試無有效值的情況
        form = CommitteeSelectForm(data={})
        self.assertFalse(form.is_valid())
        
        # 測試提供新委員姓名
        form = CommitteeSelectForm(data={'new_name': '新委員', 'new_organization': '單位'})
        self.assertTrue(form.is_valid())
