from django.test import TestCase, Client
from django.urls import reverse
from FinanceInsight.models import NewsCategory, StockMarket, StockRecommendation
from django.utils import timezone

class ViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = NewsCategory.objects.create(
            code='TW_TEST', 
            name='測試分類'
        )
        self.market = StockMarket.objects.create(
            code='TWSE_TEST', 
            name='測試股市', 
            country='Taiwan'
        )
        self.stock = StockRecommendation.objects.create(
            market=self.market,
            stock_code='2330',
            stock_name='台積電',
            current_price=500,
            recommendation_date=timezone.now().date()
        )

    def test_news_list_view(self):
        response = self.client.get(reverse('finance_insight:news_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'FinanceInsight/news_list.html')
        self.assertContains(response, '測試分類')

    def test_stock_list_view(self):
        response = self.client.get(reverse('finance_insight:stock_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'FinanceInsight/stock_recommendations.html')
        self.assertContains(response, '台積電')

    def test_stock_detail_view(self):
        response = self.client.get(reverse('finance_insight:stock_detail', args=[self.stock.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'FinanceInsight/stock_detail.html')
        self.assertContains(response, '2330')
