"""
EVCodeSigning 單元測試
測試涵蓋 Models、Forms、Validators、Services 和 Views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch, MagicMock
import json

from .models import SigningAdmin, SigningRequest, SigningFile
from .forms import SigningRequestForm, SignedFileUploadForm, RejectForm
from .validators import validate_signing_file, get_allowed_extensions_display, ALLOWED_EXTENSIONS
from .services import is_valid_email, get_system_email


# ===== Model Tests =====

class SigningAdminModelTestCase(TestCase):
    """簽章管理員模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            email='test@test.com'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.user,
            is_active=True,
            created_by=self.superuser
        )
    
    def test_signing_admin_creation(self):
        """測試簽章管理員建立"""
        self.assertEqual(self.signing_admin.user, self.user)
        self.assertTrue(self.signing_admin.is_active)
        self.assertEqual(self.signing_admin.created_by, self.superuser)
    
    def test_signing_admin_str_representation(self):
        """測試簽章管理員字串表示"""
        expected = "Test User"
        self.assertEqual(str(self.signing_admin), expected)
    
    def test_signing_admin_str_without_full_name(self):
        """測試簽章管理員字串表示 - 無全名"""
        user_no_name = User.objects.create_user(
            username='noname',
            password='testpass123'
        )
        admin = SigningAdmin.objects.create(
            user=user_no_name,
            created_by=self.superuser
        )
        self.assertEqual(str(admin), 'noname')
    
    def test_default_is_active(self):
        """測試 is_active 預設值"""
        user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        admin = SigningAdmin.objects.create(
            user=user2,
            created_by=self.superuser
        )
        self.assertTrue(admin.is_active)


class SigningRequestModelTestCase(TestCase):
    """簽章申請模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.admin_user,
            is_active=True
        )
        self.request = SigningRequest.objects.create(
            applicant=self.user,
            title='測試簽章申請',
            description='這是測試用的簽章申請說明'
        )
    
    def test_signing_request_creation(self):
        """測試簽章申請建立"""
        self.assertEqual(self.request.applicant, self.user)
        self.assertEqual(self.request.title, '測試簽章申請')
        self.assertEqual(self.request.status, 'pending')
    
    def test_signing_request_str_representation(self):
        """測試簽章申請字串表示"""
        self.assertIn('待處理', str(self.request))
        self.assertIn('測試簽章申請', str(self.request))
    
    def test_file_count_empty(self):
        """測試檔案數量 - 無檔案"""
        self.assertEqual(self.request.file_count, 0)
    
    def test_signed_file_count_empty(self):
        """測試已簽章檔案數量 - 無檔案"""
        self.assertEqual(self.request.signed_file_count, 0)
    
    def test_all_files_signed_no_files(self):
        """測試 all_files_signed - 無檔案"""
        self.assertFalse(self.request.all_files_signed)
    
    def test_mark_as_processing(self):
        """測試標記為處理中"""
        self.request.mark_as_processing(self.signing_admin)
        self.assertEqual(self.request.status, 'processing')
        self.assertEqual(self.request.assigned_admin, self.signing_admin)
    
    def test_mark_as_completed(self):
        """測試標記為已完成"""
        self.request.mark_as_completed()
        self.assertEqual(self.request.status, 'completed')
        self.assertIsNotNone(self.request.completed_at)
    
    def test_mark_as_rejected(self):
        """測試標記為已退回"""
        reason = '檔案格式不正確，請重新上傳。'
        self.request.mark_as_rejected(reason)
        self.assertEqual(self.request.status, 'rejected')
        self.assertEqual(self.request.reject_reason, reason)


class SigningFileModelTestCase(TestCase):
    """簽章檔案模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.request = SigningRequest.objects.create(
            applicant=self.user,
            title='測試申請',
            description='測試'
        )
        # 建立模擬檔案
        self.test_file = SimpleUploadedFile(
            name='test_program.exe',
            content=b'fake exe content',
            content_type='application/octet-stream'
        )
        self.signing_file = SigningFile.objects.create(
            request=self.request,
            original_file=self.test_file,
            original_filename='test_program.exe',
            file_size=16
        )
    
    def test_signing_file_creation(self):
        """測試簽章檔案建立"""
        self.assertEqual(self.signing_file.request, self.request)
        self.assertEqual(self.signing_file.original_filename, 'test_program.exe')
    
    def test_signing_file_str_representation(self):
        """測試簽章檔案字串表示"""
        self.assertEqual(str(self.signing_file), 'test_program.exe')
    
    def test_is_signed_false(self):
        """測試 is_signed - 未簽章"""
        self.assertFalse(self.signing_file.is_signed)
    
    def test_is_signed_true(self):
        """測試 is_signed - 已簽章"""
        signed_file = SimpleUploadedFile(
            name='test_program_signed.exe',
            content=b'fake signed exe content',
            content_type='application/octet-stream'
        )
        self.signing_file.signed_file = signed_file
        self.signing_file.save()
        self.assertTrue(self.signing_file.is_signed)
    
    def test_file_extension(self):
        """測試取得副檔名"""
        self.assertEqual(self.signing_file.file_extension, '.exe')
    
    def test_file_size_display_bytes(self):
        """測試檔案大小顯示 - Bytes"""
        self.signing_file.file_size = 512
        self.assertIn('B', self.signing_file.file_size_display)
    
    def test_file_size_display_kb(self):
        """測試檔案大小顯示 - KB"""
        self.signing_file.file_size = 2048
        self.assertIn('KB', self.signing_file.file_size_display)
    
    def test_file_size_display_mb(self):
        """測試檔案大小顯示 - MB"""
        self.signing_file.file_size = 1024 * 1024 * 5
        self.assertIn('MB', self.signing_file.file_size_display)
    
    def test_all_files_signed_with_files(self):
        """測試 all_files_signed - 有檔案"""
        # 未簽章
        self.assertFalse(self.request.all_files_signed)
        
        # 簽章後
        signed_file = SimpleUploadedFile(
            name='test_program_signed.exe',
            content=b'fake signed exe content',
            content_type='application/octet-stream'
        )
        self.signing_file.signed_file = signed_file
        self.signing_file.save()
        self.assertTrue(self.request.all_files_signed)


# ===== Form Tests =====

class SigningRequestFormTestCase(TestCase):
    """簽章申請表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'title': '新簽章申請',
            'description': '這是測試簽章申請的說明內容。'
        }
        form = SigningRequestForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_title(self):
        """測試無效表單 - 無標題"""
        data = {
            'title': '',
            'description': '說明內容'
        }
        form = SigningRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_invalid_form_without_description(self):
        """測試無效表單 - 無說明"""
        data = {
            'title': '標題',
            'description': ''
        }
        form = SigningRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)


class SignedFileUploadFormTestCase(TestCase):
    """簽章後檔案上傳表單測試"""
    
    def test_valid_form_with_exe(self):
        """測試有效表單 - exe 檔案"""
        file = SimpleUploadedFile(
            name='signed_program.exe',
            content=b'fake exe content',
            content_type='application/octet-stream'
        )
        form = SignedFileUploadForm(data={}, files={'signed_file': file})
        self.assertTrue(form.is_valid())
    
    def test_valid_form_with_msi(self):
        """測試有效表單 - msi 檔案"""
        file = SimpleUploadedFile(
            name='installer.msi',
            content=b'fake msi content',
            content_type='application/octet-stream'
        )
        form = SignedFileUploadForm(data={}, files={'signed_file': file})
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_with_txt(self):
        """測試無效表單 - txt 檔案"""
        file = SimpleUploadedFile(
            name='readme.txt',
            content=b'text content',
            content_type='text/plain'
        )
        form = SignedFileUploadForm(data={}, files={'signed_file': file})
        self.assertFalse(form.is_valid())
    
    def test_invalid_form_without_file(self):
        """測試無效表單 - 無檔案"""
        form = SignedFileUploadForm(data={}, files={})
        self.assertFalse(form.is_valid())


class RejectFormTestCase(TestCase):
    """退回申請表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'reason': '檔案格式不正確，請使用正確的格式重新上傳。'
        }
        form = RejectForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_reason_too_short(self):
        """測試無效表單 - 原因過短"""
        data = {
            'reason': '太短'
        }
        form = RejectForm(data=data)
        self.assertFalse(form.is_valid())
    
    def test_invalid_form_empty_reason(self):
        """測試無效表單 - 原因為空"""
        data = {
            'reason': ''
        }
        form = RejectForm(data=data)
        self.assertFalse(form.is_valid())


# ===== Validator Tests =====

class ValidatorTestCase(TestCase):
    """驗證器測試"""
    
    def test_validate_signing_file_valid_exe(self):
        """測試有效檔案 - exe"""
        file = SimpleUploadedFile(name='test.exe', content=b'content')
        # 應該不拋出異常
        validate_signing_file(file)
    
    def test_validate_signing_file_valid_msi(self):
        """測試有效檔案 - msi"""
        file = SimpleUploadedFile(name='test.msi', content=b'content')
        validate_signing_file(file)
    
    def test_validate_signing_file_valid_dll(self):
        """測試有效檔案 - dll"""
        file = SimpleUploadedFile(name='test.dll', content=b'content')
        validate_signing_file(file)
    
    def test_validate_signing_file_invalid_txt(self):
        """測試無效檔案 - txt"""
        file = SimpleUploadedFile(name='test.txt', content=b'content')
        with self.assertRaises(ValidationError):
            validate_signing_file(file)
    
    def test_validate_signing_file_invalid_pdf(self):
        """測試無效檔案 - pdf"""
        file = SimpleUploadedFile(name='document.pdf', content=b'content')
        with self.assertRaises(ValidationError):
            validate_signing_file(file)
    
    def test_get_allowed_extensions_display(self):
        """測試取得允許副檔名顯示"""
        display = get_allowed_extensions_display()
        self.assertIn('.exe', display)
        self.assertIn('.msi', display)
        self.assertIn('.dll', display)


# ===== Service Tests =====

class ServicesTestCase(TestCase):
    """服務函數測試"""
    
    def test_is_valid_email_valid(self):
        """測試有效 email"""
        self.assertTrue(is_valid_email('test@example.com'))
        self.assertTrue(is_valid_email('user.name@domain.org'))
        self.assertTrue(is_valid_email('user+tag@company.co.tw'))
    
    def test_is_valid_email_invalid(self):
        """測試無效 email"""
        self.assertFalse(is_valid_email(''))
        self.assertFalse(is_valid_email(None))
        self.assertFalse(is_valid_email('notanemail'))
        self.assertFalse(is_valid_email('missing@domain'))
        self.assertFalse(is_valid_email('@nodomain.com'))
    
    def test_get_system_email_default(self):
        """測試取得系統 email - 預設值"""
        email = get_system_email()
        self.assertIsNotNone(email)
        self.assertIn('@', email)
    
    @patch('EVCodeSigning.services.send_mail')
    def test_notify_admins_new_request_no_admins(self, mock_send_mail):
        """測試通知管理員 - 無管理員"""
        from .services import notify_admins_new_request
        user = User.objects.create_user(username='test', password='test123')
        request_obj = SigningRequest.objects.create(
            applicant=user,
            title='測試',
            description='測試'
        )
        # 無管理員時不應發送郵件
        notify_admins_new_request(request_obj)
        mock_send_mail.assert_not_called()
    
    @patch('EVCodeSigning.services.send_mail')
    def test_notify_admins_new_request_with_admins(self, mock_send_mail):
        """測試通知管理員 - 有管理員"""
        from .services import notify_admins_new_request
        user = User.objects.create_user(username='test', password='test123')
        admin_user = User.objects.create_user(
            username='admin', 
            password='admin123',
            email='admin@test.com'
        )
        SigningAdmin.objects.create(user=admin_user, is_active=True)
        request_obj = SigningRequest.objects.create(
            applicant=user,
            title='測試',
            description='測試'
        )
        notify_admins_new_request(request_obj)
        mock_send_mail.assert_called_once()
    
    @patch('EVCodeSigning.services.send_mail')
    def test_notify_applicant_completed(self, mock_send_mail):
        """測試通知申請人完成"""
        from .services import notify_applicant_completed
        user = User.objects.create_user(
            username='test', 
            password='test123',
            email='test@test.com'
        )
        request_obj = SigningRequest.objects.create(
            applicant=user,
            title='測試',
            description='測試'
        )
        request_obj.mark_as_completed()
        notify_applicant_completed(request_obj)
        mock_send_mail.assert_called_once()
    
    @patch('EVCodeSigning.services.send_mail')
    def test_notify_applicant_rejected(self, mock_send_mail):
        """測試通知申請人退回"""
        from .services import notify_applicant_rejected
        user = User.objects.create_user(
            username='test', 
            password='test123',
            email='test@test.com'
        )
        request_obj = SigningRequest.objects.create(
            applicant=user,
            title='測試',
            description='測試'
        )
        request_obj.mark_as_rejected('測試退回原因')
        notify_applicant_rejected(request_obj)
        mock_send_mail.assert_called_once()


# ===== View Tests =====

class InfoViewTestCase(TestCase):
    """說明頁面視圖測試"""
    
    def test_info_page_loads(self):
        """測試說明頁面載入"""
        response = self.client.get(reverse('evcodesigning:info'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'EVCodeSigning/info.html')


class PublicRecordListViewTestCase(TestCase):
    """公開記錄列表視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.request1 = SigningRequest.objects.create(
            applicant=self.user,
            title='申請一',
            description='說明一'
        )
        self.request2 = SigningRequest.objects.create(
            applicant=self.user,
            title='申請二',
            description='說明二',
            status='completed'
        )
    
    def test_public_records_loads(self):
        """測試公開記錄頁面載入"""
        response = self.client.get(reverse('evcodesigning:public_records'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'EVCodeSigning/public_record_list.html')
    
    def test_public_records_search(self):
        """測試公開記錄搜尋"""
        response = self.client.get(
            reverse('evcodesigning:public_records'),
            {'q': '申請一'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '申請一')
    
    def test_public_records_status_filter(self):
        """測試公開記錄狀態過濾"""
        response = self.client.get(
            reverse('evcodesigning:public_records'),
            {'status': 'completed'}
        )
        self.assertEqual(response.status_code, 200)


class SigningRequestListViewTestCase(TestCase):
    """簽章申請列表視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.admin_user,
            is_active=True
        )
        self.request1 = SigningRequest.objects.create(
            applicant=self.user,
            title='我的申請',
            description='說明'
        )
        self.request2 = SigningRequest.objects.create(
            applicant=self.other_user,
            title='別人的申請',
            description='說明'
        )
        self.client = Client()
    
    def test_request_list_requires_login(self):
        """測試需要登入"""
        response = self.client.get(reverse('evcodesigning:request_list'))
        self.assertEqual(response.status_code, 302)  # 重導向到登入頁
    
    def test_user_sees_own_requests(self):
        """測試一般使用者只能看到自己的申請"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('evcodesigning:request_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '我的申請')
        self.assertNotContains(response, '別人的申請')
    
    def test_admin_sees_all_requests(self):
        """測試管理員可以看到所有申請"""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get(reverse('evcodesigning:request_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '我的申請')
        self.assertContains(response, '別人的申請')


class SigningRequestDetailViewTestCase(TestCase):
    """簽章申請詳情視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.request = SigningRequest.objects.create(
            applicant=self.user,
            title='測試申請',
            description='說明'
        )
        self.client = Client()
    
    def test_detail_requires_login(self):
        """測試需要登入"""
        response = self.client.get(
            reverse('evcodesigning:request_detail', kwargs={'pk': self.request.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_owner_can_view_detail(self):
        """測試申請人可以查看詳情"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('evcodesigning:request_detail', kwargs={'pk': self.request.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試申請')
    
    def test_other_user_cannot_view_detail(self):
        """測試其他使用者無法查看詳情"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('evcodesigning:request_detail', kwargs={'pk': self.request.pk})
        )
        self.assertEqual(response.status_code, 404)


class SigningRequestCreateViewTestCase(TestCase):
    """建立簽章申請視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
    
    def test_create_requires_login(self):
        """測試需要登入"""
        response = self.client.get(reverse('evcodesigning:request_create'))
        self.assertEqual(response.status_code, 302)
    
    def test_create_form_loads(self):
        """測試建立表單載入"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('evcodesigning:request_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'EVCodeSigning/request_form.html')
    
    @patch('EVCodeSigning.views.notify_admins_new_request')
    def test_create_request_success(self, mock_notify):
        """測試成功建立申請"""
        self.client.login(username='testuser', password='testpass123')
        
        file = SimpleUploadedFile(
            name='test.exe',
            content=b'fake exe content',
            content_type='application/octet-stream'
        )
        
        response = self.client.post(
            reverse('evcodesigning:request_create'),
            {
                'title': '新的簽章申請',
                'description': '這是簽章申請的詳細說明。',
                'files': file
            }
        )
        
        # 應該重導向到詳情頁
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SigningRequest.objects.filter(title='新的簽章申請').exists())
    
    def test_create_request_without_files_fails(self):
        """測試無檔案時建立失敗"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('evcodesigning:request_create'),
            {
                'title': '新的簽章申請',
                'description': '這是簽章申請的詳細說明。'
            }
        )
        
        # 應該返回表單頁面並顯示錯誤
        self.assertEqual(response.status_code, 200)


class AdminPendingListViewTestCase(TestCase):
    """管理員待處理列表視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.admin_user,
            is_active=True
        )
        self.pending_request = SigningRequest.objects.create(
            applicant=self.user,
            title='待處理申請',
            description='說明',
            status='pending'
        )
        self.completed_request = SigningRequest.objects.create(
            applicant=self.user,
            title='已完成申請',
            description='說明',
            status='completed'
        )
        self.client = Client()
    
    def test_non_admin_redirected(self):
        """測試非管理員被重導向"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('evcodesigning:admin_pending'))
        self.assertEqual(response.status_code, 302)
    
    def test_admin_can_view(self):
        """測試管理員可以查看"""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get(reverse('evcodesigning:admin_pending'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '待處理申請')


class FileDownloadViewTestCase(TestCase):
    """檔案下載視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.admin_user,
            is_active=True
        )
        self.request = SigningRequest.objects.create(
            applicant=self.user,
            title='測試申請',
            description='說明'
        )
        self.test_file = SimpleUploadedFile(
            name='test.exe',
            content=b'fake exe content',
            content_type='application/octet-stream'
        )
        self.signing_file = SigningFile.objects.create(
            request=self.request,
            original_file=self.test_file,
            original_filename='test.exe',
            file_size=16
        )
        self.client = Client()
    
    def test_download_original_requires_admin(self):
        """測試下載原始檔案需要管理員權限"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('evcodesigning:download_original', kwargs={'pk': self.signing_file.pk})
        )
        # 應該重導向（非管理員無權限）
        self.assertEqual(response.status_code, 302)
    
    def test_download_signed_owner_can_access(self):
        """測試申請人可以下載簽章後檔案"""
        # 先上傳簽章後檔案
        signed_file = SimpleUploadedFile(
            name='test_signed.exe',
            content=b'fake signed exe content',
            content_type='application/octet-stream'
        )
        self.signing_file.signed_file = signed_file
        self.signing_file.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('evcodesigning:download_signed', kwargs={'pk': self.signing_file.pk})
        )
        # 應該成功下載
        self.assertEqual(response.status_code, 200)


class SigningActionViewTestCase(TestCase):
    """簽章操作視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.admin_user,
            is_active=True
        )
        self.request = SigningRequest.objects.create(
            applicant=self.user,
            title='測試申請',
            description='說明'
        )
        self.test_file = SimpleUploadedFile(
            name='test.exe',
            content=b'fake exe content',
            content_type='application/octet-stream'
        )
        self.signing_file = SigningFile.objects.create(
            request=self.request,
            original_file=self.test_file,
            original_filename='test.exe',
            file_size=16
        )
        self.client = Client()
    
    @patch('EVCodeSigning.views.notify_applicant_completed')
    def test_complete_signing_requires_all_files_signed(self, mock_notify):
        """測試完成簽章需要所有檔案都已簽章"""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.post(
            reverse('evcodesigning:complete_signing', kwargs={'pk': self.request.pk})
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    @patch('EVCodeSigning.views.notify_applicant_completed')
    def test_complete_signing_success(self, mock_notify):
        """測試成功完成簽章"""
        # 先上傳簽章後檔案
        signed_file = SimpleUploadedFile(
            name='test_signed.exe',
            content=b'fake signed exe content',
            content_type='application/octet-stream'
        )
        self.signing_file.signed_file = signed_file
        self.signing_file.save()
        
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.post(
            reverse('evcodesigning:complete_signing', kwargs={'pk': self.request.pk})
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    @patch('EVCodeSigning.views.notify_applicant_rejected')
    def test_reject_request(self, mock_notify):
        """測試退回申請"""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.post(
            reverse('evcodesigning:reject_request', kwargs={'pk': self.request.pk}),
            {'reason': '檔案格式不正確，請使用正確的格式重新上傳。'}
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_reject_request_requires_reason(self):
        """測試退回申請需要填寫原因"""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.post(
            reverse('evcodesigning:reject_request', kwargs={'pk': self.request.pk}),
            {'reason': '太短'}
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class SuperuserAdminManageViewTestCase(TestCase):
    """超級使用者管理員管理視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.superuser = User.objects.create_superuser(
            username='superadmin',
            password='admin123',
            email='super@test.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.candidate_user = User.objects.create_user(
            username='candidate',
            password='testpass123',
            first_name='Candidate',
            last_name='User'
        )
        self.client = Client()
    
    def test_admin_manage_requires_superuser(self):
        """測試管理員管理頁面需要 superuser"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('evcodesigning:admin_manage'))
        self.assertEqual(response.status_code, 302)
    
    def test_superuser_can_access_admin_manage(self):
        """測試 superuser 可以存取管理員管理頁面"""
        self.client.login(username='superadmin', password='admin123')
        response = self.client.get(reverse('evcodesigning:admin_manage'))
        self.assertEqual(response.status_code, 200)
    
    def test_search_users_requires_superuser(self):
        """測試搜尋使用者需要 superuser"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('evcodesigning:search_users_for_admin'),
            {'q': 'cand'}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_search_users_by_superuser(self):
        """測試 superuser 搜尋使用者"""
        self.client.login(username='superadmin', password='admin123')
        response = self.client.get(
            reverse('evcodesigning:search_users_for_admin'),
            {'q': 'candidate'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data['users']) > 0)
    
    def test_add_signing_admin(self):
        """測試新增簽章管理員"""
        self.client.login(username='superadmin', password='admin123')
        response = self.client.post(
            reverse('evcodesigning:add_signing_admin'),
            {'user_id': self.candidate_user.pk}
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(SigningAdmin.objects.filter(user=self.candidate_user).exists())
    
    def test_remove_signing_admin(self):
        """測試移除簽章管理員"""
        admin = SigningAdmin.objects.create(
            user=self.candidate_user,
            is_active=True
        )
        self.client.login(username='superadmin', password='admin123')
        response = self.client.post(
            reverse('evcodesigning:remove_signing_admin', kwargs={'pk': admin.pk})
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(SigningAdmin.objects.filter(user=self.candidate_user).exists())
    
    def test_toggle_signing_admin(self):
        """測試切換簽章管理員狀態"""
        admin = SigningAdmin.objects.create(
            user=self.candidate_user,
            is_active=True
        )
        self.client.login(username='superadmin', password='admin123')
        response = self.client.post(
            reverse('evcodesigning:toggle_signing_admin', kwargs={'pk': admin.pk})
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(data['is_active'])
        
        # 再次切換
        response = self.client.post(
            reverse('evcodesigning:toggle_signing_admin', kwargs={'pk': admin.pk})
        )
        data = json.loads(response.content)
        self.assertTrue(data['is_active'])


class UploadSignedFileViewTestCase(TestCase):
    """上傳簽章後檔案視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123'
        )
        self.signing_admin = SigningAdmin.objects.create(
            user=self.admin_user,
            is_active=True
        )
        self.request = SigningRequest.objects.create(
            applicant=self.user,
            title='測試申請',
            description='說明'
        )
        self.test_file = SimpleUploadedFile(
            name='test.exe',
            content=b'fake exe content',
            content_type='application/octet-stream'
        )
        self.signing_file = SigningFile.objects.create(
            request=self.request,
            original_file=self.test_file,
            original_filename='test.exe',
            file_size=16
        )
        self.client = Client()
    
    def test_upload_requires_admin(self):
        """測試上傳需要管理員權限"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('evcodesigning:upload_signed', kwargs={'pk': self.signing_file.pk})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_upload_signed_file_success(self):
        """測試成功上傳簽章後檔案"""
        self.client.login(username='adminuser', password='testpass123')
        
        signed_file = SimpleUploadedFile(
            name='test_signed.exe',
            content=b'fake signed exe content',
            content_type='application/octet-stream'
        )
        
        response = self.client.post(
            reverse('evcodesigning:upload_signed', kwargs={'pk': self.signing_file.pk}),
            {'signed_file': signed_file}
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_upload_invalid_method(self):
        """測試無效的請求方法"""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get(
            reverse('evcodesigning:upload_signed', kwargs={'pk': self.signing_file.pk})
        )
        self.assertEqual(response.status_code, 405)
