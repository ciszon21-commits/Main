from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Category, Achievement, ViewLog, Comment


class DevShowcaseTestCase(TestCase):
    def setUp(self):
        """設定測試資料"""
        # 建立測試使用者
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 建立測試分類
        self.category = Category.objects.create(
            name='測試分類',
            description='這是測試分類',
            order=1
        )
        
        # 建立測試成果
        self.achievement = Achievement.objects.create(
            name='測試成果',
            category=self.category,
            summary='這是一個測試成果的簡介',
            created_by=self.user
        )
        
        self.client = Client()

    def test_category_creation(self):
        """測試分類建立"""
        self.assertEqual(self.category.name, '測試分類')
        self.assertEqual(self.category.order, 1)

    def test_achievement_creation(self):
        """測試成果建立"""
        self.assertEqual(self.achievement.name, '測試成果')
        self.assertEqual(self.achievement.category, self.category)
        self.assertEqual(self.achievement.created_by, self.user)

    def test_achievement_list_view(self):
        """測試成果列表頁面"""
        response = self.client.get('/showcase/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '開發成果展示')

    def test_view_log_creation(self):
        """測試瀏覽記錄"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/showcase/achievement/{self.achievement.id}/')
        
        # 檢查瀏覽記錄是否建立
        view_log = ViewLog.objects.filter(
            achievement=self.achievement,
            user=self.user
        ).first()
        self.assertIsNotNone(view_log)

    def test_comment_creation(self):
        """測試留言建立"""
        comment = Comment.objects.create(
            achievement=self.achievement,
            user=self.user,
            content='這是一則測試留言'
        )
        self.assertEqual(comment.content, '這是一則測試留言')
        self.assertEqual(comment.achievement, self.achievement)
