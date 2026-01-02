"""
NewsSubscriber 單元測試
測試涵蓋 Models、Views 和 Utility Functions
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from .models import Topic, Keyword, NewsItem, DailySummary, Subscription, OpenAIResponse


# ===== Model Tests =====

class TopicModelTestCase(TestCase):
    """主題模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.topic = Topic.objects.create(name='測試主題')
    
    def test_topic_creation(self):
        """測試主題建立"""
        self.assertEqual(self.topic.name, '測試主題')
        self.assertIsNotNone(self.topic.created_at)
    
    def test_topic_str_representation(self):
        """測試主題字串表示"""
        self.assertEqual(str(self.topic), '測試主題')
    
    def test_topic_ordering(self):
        """測試主題排序 - 按建立時間降序"""
        import time
        time.sleep(0.01)  # 確保 created_at 不同
        topic2 = Topic.objects.create(name='新主題')
        topics = Topic.objects.all()
        # ID 較大的在前 (較新建立)
        self.assertEqual(topics[0].pk, topic2.pk)


class KeywordModelTestCase(TestCase):
    """關鍵字模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.topic = Topic.objects.create(name='測試主題')
        self.keyword = Keyword.objects.create(
            topic=self.topic,
            word='AI新聞'
        )
    
    def test_keyword_creation(self):
        """測試關鍵字建立"""
        self.assertEqual(self.keyword.word, 'AI新聞')
        self.assertEqual(self.keyword.topic, self.topic)
    
    def test_keyword_str_representation(self):
        """測試關鍵字字串表示"""
        expected = '測試主題 - AI新聞'
        self.assertEqual(str(self.keyword), expected)
    
    def test_keyword_topic_relationship(self):
        """測試關鍵字與主題的關聯"""
        self.assertIn(self.keyword, self.topic.keywords.all())


class NewsItemModelTestCase(TestCase):
    """新聞項目模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.topic = Topic.objects.create(name='測試主題')
        self.news_item = NewsItem.objects.create(
            topic=self.topic,
            title='AI技術新突破',
            date=timezone.now(),
            url='https://example.com/news/1',
            source='科技日報',
            content='新聞內容',
            summary='新聞摘要'
        )
    
    def test_news_item_creation(self):
        """測試新聞項目建立"""
        self.assertEqual(self.news_item.title, 'AI技術新突破')
        self.assertEqual(self.news_item.source, '科技日報')
        self.assertEqual(self.news_item.topic, self.topic)
    
    def test_news_item_str_representation(self):
        """測試新聞項目字串表示"""
        self.assertEqual(str(self.news_item), 'AI技術新突破')
    
    def test_news_item_ordering(self):
        """測試新聞項目排序 - 按發布日期降序"""
        older_news = NewsItem.objects.create(
            topic=self.topic,
            title='舊新聞',
            date=timezone.now() - timedelta(days=1),
            url='https://example.com/news/2',
            source='科技日報'
        )
        news_items = NewsItem.objects.all()
        self.assertEqual(news_items[0], self.news_item)  # 較新的在前


class DailySummaryModelTestCase(TestCase):
    """每日摘要模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.topic = Topic.objects.create(name='測試主題')
        self.summary = DailySummary.objects.create(
            topic=self.topic,
            summary='這是每日新聞摘要',
            news_source_html='<div>來源HTML</div>',
            date=timezone.now().date(),
            news_count=5
        )
    
    def test_daily_summary_creation(self):
        """測試每日摘要建立"""
        self.assertEqual(self.summary.summary, '這是每日新聞摘要')
        self.assertEqual(self.summary.news_count, 5)
    
    def test_daily_summary_str_representation(self):
        """測試每日摘要字串表示"""
        today = timezone.now().date()
        expected = f'測試主題 - {today}'
        self.assertEqual(str(self.summary), expected)
    
    def test_daily_summary_unique_together(self):
        """測試 unique_together 約束"""
        with self.assertRaises(IntegrityError):
            DailySummary.objects.create(
                topic=self.topic,
                summary='重複摘要',
                date=self.summary.date
            )
    
    def test_daily_summary_ordering(self):
        """測試每日摘要排序 - 按日期降序"""
        yesterday = timezone.now().date() - timedelta(days=1)
        older_summary = DailySummary.objects.create(
            topic=self.topic,
            summary='昨日摘要',
            date=yesterday
        )
        summaries = DailySummary.objects.all()
        self.assertEqual(summaries[0], self.summary)  # 較新的在前


class SubscriptionModelTestCase(TestCase):
    """訂閱模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.topic = Topic.objects.create(name='測試主題')
        self.subscription = Subscription.objects.create(
            user=self.user,
            topic=self.topic,
            email='test@example.com',
            is_active=True
        )
    
    def test_subscription_creation(self):
        """測試訂閱建立"""
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.topic, self.topic)
        self.assertTrue(self.subscription.is_active)
    
    def test_subscription_str_representation(self):
        """測試訂閱字串表示"""
        expected = 'testuser - 測試主題'
        self.assertEqual(str(self.subscription), expected)
    
    def test_subscription_unique_together(self):
        """測試 unique_together 約束"""
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(
                user=self.user,
                topic=self.topic,
                email='other@example.com'
            )
    
    def test_subscription_default_is_active(self):
        """測試 is_active 預設值"""
        user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        topic2 = Topic.objects.create(name='主題2')
        sub = Subscription.objects.create(
            user=user2,
            topic=topic2,
            email='user2@example.com'
        )
        self.assertTrue(sub.is_active)


class OpenAIResponseModelTestCase(TestCase):
    """OpenAI 回應模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.response = OpenAIResponse.objects.create(
            request_id='req-12345',
            model='gpt-4',
            content='這是AI生成的回應',
            created=timezone.now(),
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            tag='新聞摘要'
        )
    
    def test_openai_response_creation(self):
        """測試 OpenAI 回應建立"""
        self.assertEqual(self.response.request_id, 'req-12345')
        self.assertEqual(self.response.model, 'gpt-4')
        self.assertEqual(self.response.total_tokens, 300)
    
    def test_openai_response_str_representation(self):
        """測試 OpenAI 回應字串表示"""
        self.assertIn('gpt-4', str(self.response))
    
    def test_openai_response_default_tag(self):
        """測試預設 tag 值"""
        response = OpenAIResponse.objects.create(
            request_id='req-67890',
            model='gpt-3.5',
            content='內容',
            created=timezone.now(),
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150
        )
        self.assertEqual(response.tag, 'NA')


# ===== View Tests =====

class TopicListViewTestCase(TestCase):
    """主題列表視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.topic = Topic.objects.create(name='測試主題')
        self.subscription = Subscription.objects.create(
            user=self.user,
            topic=self.topic,
            email='test@example.com',
            is_active=True
        )
    
    def test_topic_list_loads(self):
        """測試主題列表頁面載入"""
        response = self.client.get(reverse('news_subscriber:topic_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試主題')
    
    def test_topic_list_anonymous_no_subscriptions(self):
        """測試匿名使用者訂閱狀態為空"""
        response = self.client.get(reverse('news_subscriber:topic_list'))
        self.assertEqual(response.context['subscribed_topics'], [])
    
    def test_topic_list_authenticated_with_subscriptions(self):
        """測試已登入使用者顯示訂閱狀態"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('news_subscriber:topic_list'))
        self.assertIn(self.topic.pk, response.context['subscribed_topics'])


class TopicDetailViewTestCase(TestCase):
    """主題詳情視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.topic = Topic.objects.create(name='測試主題')
        self.keyword = Keyword.objects.create(topic=self.topic, word='AI')
        self.news_item = NewsItem.objects.create(
            topic=self.topic,
            title='測試新聞',
            date=timezone.now(),
            url='https://example.com/news1',
            source='來源'
        )
        self.summary = DailySummary.objects.create(
            topic=self.topic,
            summary='今日摘要',
            date=timezone.now().date()
        )
    
    def test_topic_detail_loads(self):
        """測試主題詳情頁面載入"""
        response = self.client.get(
            reverse('news_subscriber:topic_detail', kwargs={'pk': self.topic.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試主題')
    
    def test_topic_detail_context_news_items(self):
        """測試 context 包含新聞項目"""
        response = self.client.get(
            reverse('news_subscriber:topic_detail', kwargs={'pk': self.topic.pk})
        )
        self.assertIn(self.news_item, response.context['news_items'])
    
    def test_topic_detail_context_today_summary(self):
        """測試 context 包含今日摘要"""
        response = self.client.get(
            reverse('news_subscriber:topic_detail', kwargs={'pk': self.topic.pk})
        )
        self.assertEqual(response.context['today_summary'], self.summary)


class TopicCreateViewTestCase(TestCase):
    """建立主題視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_topic_create_get(self):
        """測試建立主題頁面 - GET"""
        response = self.client.get(reverse('news_subscriber:topic_add'))
        self.assertEqual(response.status_code, 200)
    
    def test_topic_create_post_valid(self):
        """測試建立主題 - POST 有效資料"""
        response = self.client.post(
            reverse('news_subscriber:topic_add'),
            {'name': '新主題'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Topic.objects.filter(name='新主題').exists())
    
    def test_topic_create_auto_subscribe_with_email(self):
        """測試建立主題 - 已登入且有email會自動訂閱"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:topic_add'),
            {'name': '自動訂閱主題'}
        )
        self.assertEqual(response.status_code, 302)
        topic = Topic.objects.get(name='自動訂閱主題')
        self.assertTrue(
            Subscription.objects.filter(user=self.user, topic=topic).exists()
        )
    
    def test_topic_create_no_subscribe_without_email(self):
        """測試建立主題 - 無email不自動訂閱"""
        user_no_email = User.objects.create_user(
            username='noemail',
            password='testpass123'
        )
        self.client.login(username='noemail', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:topic_add'),
            {'name': '不訂閱主題'}
        )
        self.assertEqual(response.status_code, 302)
        topic = Topic.objects.get(name='不訂閱主題')
        self.assertFalse(
            Subscription.objects.filter(user=user_no_email, topic=topic).exists()
        )


class KeywordCreateViewTestCase(TestCase):
    """建立關鍵字視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.topic = Topic.objects.create(name='測試主題')
    
    def test_keyword_create_get(self):
        """測試建立關鍵字頁面 - GET"""
        response = self.client.get(
            reverse('news_subscriber:keyword_add', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['topic'], self.topic)
    
    def test_keyword_create_post_valid(self):
        """測試建立關鍵字 - POST 有效資料"""
        response = self.client.post(
            reverse('news_subscriber:keyword_add', kwargs={'topic_id': self.topic.pk}),
            {'word': '新關鍵字'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Keyword.objects.filter(topic=self.topic, word='新關鍵字').exists()
        )


class SubscribeViewTestCase(TestCase):
    """訂閱視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user_no_email = User.objects.create_user(
            username='noemail',
            password='testpass123'
        )
        self.topic = Topic.objects.create(name='測試主題')
    
    def test_subscribe_requires_login(self):
        """測試訂閱需要登入"""
        response = self.client.post(
            reverse('news_subscriber:subscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_subscribe_requires_post(self):
        """測試訂閱需要 POST 方法"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('news_subscriber:subscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 405)
    
    def test_subscribe_success(self):
        """測試訂閱成功"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:subscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Subscription.objects.filter(user=self.user, topic=self.topic, is_active=True).exists()
        )
    
    def test_subscribe_without_email_fails(self):
        """測試無 email 時訂閱失敗"""
        self.client.login(username='noemail', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:subscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Subscription.objects.filter(user=self.user_no_email, topic=self.topic).exists()
        )
    
    def test_resubscribe_inactive_subscription(self):
        """測試重新啟用已停用的訂閱"""
        Subscription.objects.create(
            user=self.user,
            topic=self.topic,
            email='old@example.com',
            is_active=False
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:subscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        sub = Subscription.objects.get(user=self.user, topic=self.topic)
        self.assertTrue(sub.is_active)
        self.assertEqual(sub.email, 'test@example.com')  # email 應被更新


class UnsubscribeViewTestCase(TestCase):
    """取消訂閱視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.topic = Topic.objects.create(name='測試主題')
        self.subscription = Subscription.objects.create(
            user=self.user,
            topic=self.topic,
            email='test@example.com',
            is_active=True
        )
    
    def test_unsubscribe_requires_login(self):
        """測試取消訂閱需要登入"""
        response = self.client.post(
            reverse('news_subscriber:unsubscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_unsubscribe_requires_post(self):
        """測試取消訂閱需要 POST 方法"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('news_subscriber:unsubscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 405)
    
    def test_unsubscribe_success(self):
        """測試取消訂閱成功"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:unsubscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        sub = Subscription.objects.get(user=self.user, topic=self.topic)
        self.assertFalse(sub.is_active)
    
    def test_unsubscribe_nonexistent(self):
        """測試取消不存在的訂閱"""
        self.subscription.delete()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:unsubscribe_topic', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)  # 仍然重導向，顯示訊息


class FetchNewsViewTestCase(TestCase):
    """擷取新聞視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.topic = Topic.objects.create(name='測試主題')
        Keyword.objects.create(topic=self.topic, word='AI')
    
    def test_fetch_news_requires_login(self):
        """測試擷取新聞需要登入"""
        response = self.client.post(
            reverse('news_subscriber:fetch_topic_news', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_fetch_news_requires_post(self):
        """測試擷取新聞需要 POST 方法"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('news_subscriber:fetch_topic_news', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 405)
    
    @patch('NewsSubscriber.utils.news_fetcher.fetch_news_for_topic')
    def test_fetch_news_success(self, mock_fetch):
        """測試擷取新聞成功"""
        mock_fetch.return_value = {
            'success': True,
            'message': '新聞擷取成功',
            'news_count': 10
        }
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:fetch_topic_news', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
        mock_fetch.assert_called_once()
    
    @patch('NewsSubscriber.utils.news_fetcher.fetch_news_for_topic')
    def test_fetch_news_failure(self, mock_fetch):
        """測試擷取新聞失敗"""
        mock_fetch.return_value = {
            'success': False,
            'message': '擷取失敗',
            'news_count': 0
        }
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:fetch_topic_news', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    @patch('NewsSubscriber.utils.news_fetcher.fetch_news_for_topic')
    def test_fetch_news_exception(self, mock_fetch):
        """測試擷取新聞發生異常"""
        mock_fetch.side_effect = Exception('API 錯誤')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('news_subscriber:fetch_topic_news', kwargs={'topic_id': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)


# ===== Utility Tests =====





class NewsFetcherTestCase(TestCase):
    """新聞擷取工具函數測試"""
    
    def test_parse_date_with_published(self):
        """測試 _parse_date 有 published 屬性"""
        from NewsSubscriber.utils.news_fetcher import _parse_date
        
        entry = MagicMock()
        entry.published = 'Wed, 01 Jan 2025 12:00:00 GMT'
        
        result = _parse_date(entry)
        
        self.assertIsNotNone(result)
    
    def test_parse_date_fallback(self):
        """測試 _parse_date 回退到當前時間"""
        from NewsSubscriber.utils.news_fetcher import _parse_date
        
        entry = MagicMock(spec=[])  # 無 published 屬性
        
        result = _parse_date(entry)
        
        self.assertIsNotNone(result)
    
    def test_extract_source_from_title(self):
        """測試 _extract_source 從標題提取來源"""
        from NewsSubscriber.utils.news_fetcher import _extract_source
        
        entry = {'title': 'AI新突破 - 科技日報'}
        
        result = _extract_source(entry)
        
        self.assertEqual(result, '科技日報')
    
    def test_extract_source_from_source_attr(self):
        """測試 _extract_source 從 source 屬性提取"""
        from NewsSubscriber.utils.news_fetcher import _extract_source
        
        entry = MagicMock()
        entry.get.return_value = 'AI新突破'  # 無 " - " 分隔
        entry.source = MagicMock()
        entry.source.title = '新聞網站'
        
        result = _extract_source(entry)
        
        self.assertEqual(result, '新聞網站')
    
    def test_extract_source_default(self):
        """測試 _extract_source 預設值"""
        from NewsSubscriber.utils.news_fetcher import _extract_source
        
        entry = {'title': 'AI新突破'}  # 無來源資訊
        
        result = _extract_source(entry)
        
        self.assertEqual(result, 'Google News')
    
    def test_deduplicate_news_empty(self):
        """測試 _deduplicate_news 空列表"""
        from NewsSubscriber.utils.news_fetcher import _deduplicate_news
        
        result = _deduplicate_news([], None)
        
        self.assertEqual(result, [])
    
    def test_deduplicate_news_removes_duplicates(self):
        """測試 _deduplicate_news 移除重複"""
        from NewsSubscriber.utils.news_fetcher import _deduplicate_news
        
        topic = Topic.objects.create(name='測試')
        news_list = [
            {'title': 'AI新突破', 'url': 'https://example.com/1', 'date': timezone.now(), 'source': 'A'},
            {'title': 'AI新突破', 'url': 'https://example.com/2', 'date': timezone.now(), 'source': 'B'},  # 相似標題
        ]
        
        result = _deduplicate_news(news_list, topic)
        
        self.assertEqual(len(result), 1)
    
    def test_deduplicate_news_removes_same_url(self):
        """測試 _deduplicate_news 移除相同 URL"""
        from NewsSubscriber.utils.news_fetcher import _deduplicate_news
        
        topic = Topic.objects.create(name='測試')
        news_list = [
            {'title': 'AI新突破1', 'url': 'https://example.com/1', 'date': timezone.now(), 'source': 'A'},
            {'title': 'AI新突破2', 'url': 'https://example.com/1', 'date': timezone.now(), 'source': 'B'},  # 相同URL
        ]
        
        result = _deduplicate_news(news_list, topic)
        
        self.assertEqual(len(result), 1)
    
    @patch('NewsSubscriber.utils.news_fetcher._fetch_google_news')
    @patch('NewsSubscriber.utils.news_fetcher._generate_daily_summary')
    def test_fetch_news_for_topic_no_keywords(self, mock_summary, mock_fetch):
        """測試 fetch_news_for_topic 無關鍵字"""
        from NewsSubscriber.utils.news_fetcher import fetch_news_for_topic
        
        topic = Topic.objects.create(name='無關鍵字主題')
        
        result = fetch_news_for_topic(topic)
        
        self.assertFalse(result['success'])
        self.assertIn('沒有關鍵字', result['message'])
    
    @patch('NewsSubscriber.utils.news_fetcher._fetch_google_news')
    @patch('NewsSubscriber.utils.news_fetcher._generate_daily_summary')
    def test_fetch_news_for_topic_success(self, mock_summary, mock_fetch):
        """測試 fetch_news_for_topic 成功"""
        from NewsSubscriber.utils.news_fetcher import fetch_news_for_topic
        
        topic = Topic.objects.create(name='測試主題')
        Keyword.objects.create(topic=topic, word='AI')
        
        mock_fetch.return_value = [
            {'title': 'AI新聞', 'url': 'https://example.com/1', 'date': timezone.now(), 'source': '來源', 'topic': topic}
        ]
        mock_summary.return_value = '<p>摘要</p>'
        
        result = fetch_news_for_topic(topic)
        
        self.assertTrue(result['success'])
        self.assertGreater(result['news_count'], 0)
