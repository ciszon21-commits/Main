from django.test import TestCase
from django.utils import timezone
from FinanceInsight.models import NewsCategory, FinancialNews, StockMarket, StockRecommendation, DailyNewsSummary
from datetime import date

class NewsModelTest(TestCase):
    def setUp(self):
        self.category = NewsCategory.objects.create(
            code='TW_TEST',
            name='測試分類',
            description='測試用'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, '測試分類')
        self.assertEqual(str(self.category), '測試分類')

    def test_news_creation(self):
        news = FinancialNews.objects.create(
            category=self.category,
            title='測試新聞',
            source='測試來源',
            source_url='http://example.com',
            content='新聞內容',
            published_at=timezone.now()
        )
        self.assertEqual(news.title, '測試新聞')
        self.assertEqual(news.category, self.category)

    def test_daily_summary(self):
        summary = DailyNewsSummary.objects.create(
            category=self.category,
            date=date.today(),
            summary='今日摘要',
            conclusion='今日總結',
            news_count=10
        )
        self.assertEqual(summary.news_count, 10)
        # Test unique constraint
        # (This depends on db setup, usually IntegrityError)

class StockModelTest(TestCase):
    def setUp(self):
        self.market = StockMarket.objects.create(
            code='TWSE_TEST',
            name='測試股市',
            country='Taiwan'
        )

    def test_recommendation_creation(self):
        stock = StockRecommendation.objects.create(
            market=self.market,
            stock_code='2330',
            stock_name='台積電',
            current_price=500.00,
            price_change=10.00,
            price_change_percent=2.00,
            recommendation_reason='好公司'
        )
        self.assertEqual(str(stock), '2330 - 台積電')
        self.assertEqual(stock.market, self.market)
