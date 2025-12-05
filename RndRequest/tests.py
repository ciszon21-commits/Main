from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import RndRequest, RndRequestVote


class RndRequestModelTestCase(TestCase):
    """RndRequest Model 測試"""
    
    def setUp(self):
        """設定測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        self.request = RndRequest.objects.create(
            title='測試需求',
            demand_quantity='每周使用 4 小時，需求人數約 10 人',
            data_source='來自 ERP 系統的出貨報表',
            processing_flow='<p>1. 登入系統</p><p>2. 選擇報表</p><p>3. 匯出資料</p>',
            expected_outcome='可節省每周 5 小時人工作業時間',
            priority_level='high',
            created_by=self.user
        )
        
        self.client = Client()

    def test_request_creation(self):
        """測試需求建立"""
        self.assertEqual(self.request.title, '測試需求')
        self.assertEqual(self.request.priority_level, 'high')
        self.assertEqual(self.request.status, 'pending')
        self.assertEqual(self.request.created_by, self.user)

    def test_vote_creation(self):
        """測試投票建立"""
        vote = RndRequestVote.objects.create(
            request=self.request,
            user=self.user,
            vote_type=1
        )
        self.assertEqual(vote.vote_type, 1)
        self.assertEqual(vote.request, self.request)
        self.assertEqual(vote.user, self.user)

    def test_vote_score_calculation(self):
        """測試淨票數計算"""
        self.assertEqual(self.request.vote_score, 0)
        
        RndRequestVote.objects.create(
            request=self.request,
            user=self.user,
            vote_type=1
        )
        self.assertEqual(self.request.vote_score, 1)
        
        RndRequestVote.objects.create(
            request=self.request,
            user=self.user2,
            vote_type=-1
        )
        self.assertEqual(self.request.vote_score, 0)

    def test_unique_vote_constraint(self):
        """測試一人一票限制（直接建立會觸發約束）"""
        RndRequestVote.objects.create(
            request=self.request,
            user=self.user,
            vote_type=1
        )
        
        with self.assertRaises(Exception):
            RndRequestVote.objects.create(
                request=self.request,
                user=self.user,
                vote_type=-1
            )


class RndRequestVoteAPITestCase(TestCase):
    """投票 API 測試"""
    
    def setUp(self):
        """設定測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.request = RndRequest.objects.create(
            title='測試需求',
            demand_quantity='每周使用 4 小時',
            data_source='ERP 系統',
            processing_flow='<p>測試流程</p>',
            created_by=self.user
        )
        
        self.client = Client()

    def test_vote_api_requires_login(self):
        """測試投票 API 需要登入"""
        response = self.client.post(
            f'/rnd-request/{self.request.id}/vote/',
            {'vote_type': 1}
        )
        self.assertEqual(response.status_code, 302)

    def test_vote_api_authenticated(self):
        """測試已登入使用者投票"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            f'/rnd-request/{self.request.id}/vote/',
            {'vote_type': 1}
        )
        self.assertEqual(response.status_code, 200)
        vote = RndRequestVote.objects.get(request=self.request, user=self.user)
        self.assertEqual(vote.vote_type, 1)

    def test_vote_api_change_vote(self):
        """測試更改投票（新功能）"""
        self.client.login(username='testuser', password='testpass123')
        
        # 第一次投票（贊成）
        response = self.client.post(
            f'/rnd-request/{self.request.id}/vote/',
            {'vote_type': 1}
        )
        self.assertEqual(response.status_code, 200)
        
        # 改為反對票應該成功
        response = self.client.post(
            f'/rnd-request/{self.request.id}/vote/',
            {'vote_type': -1}
        )
        self.assertEqual(response.status_code, 200)
        
        # 確認投票已更改
        vote = RndRequestVote.objects.get(request=self.request, user=self.user)
        self.assertEqual(vote.vote_type, -1)
