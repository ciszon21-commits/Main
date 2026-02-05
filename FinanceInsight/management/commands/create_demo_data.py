from django.core.management.base import BaseCommand
from django.utils import timezone
from FinanceInsight.models import NewsCategory, FinancialNews, DailyNewsSummary, StockMarket, StockRecommendation, StockTrend
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create demo data for FinanceInsight app'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')
        
        # Ensure init data exists
        if not NewsCategory.objects.exists() or not StockMarket.objects.exists():
            self.stdout.write(self.style.WARNING('Please run init_finance_data first.'))
            return

        today = timezone.now().date()
        
        # 1. Create Demo News
        tw_cat = NewsCategory.objects.get(code='TW_FINANCE')
        us_cat = NewsCategory.objects.get(code='US_FINANCE')
        
        tw_news = [
            ("台積電法說會前夕 外資調高目標價", "隨著AI需求強勁，外資看好台積電先進製程產能利用率...", "鉅亨網"),
            ("台股大漲200點 站上萬九大關", "受美股大漲激勵，台股今日開高走高...", "經濟日報"),
            ("航運股表現強勢 長榮陽明領軍", "紅海危機未解，運價維持高檔...", "工商時報"),
        ]
        
        for title, content, source in tw_news:
            FinancialNews.objects.get_or_create(
                title=title,
                defaults={
                    'category': tw_cat,
                    'content': content,
                    'source': source,
                    'source_url': 'https://example.com',
                    'published_at': timezone.now()
                }
            )

        us_news = [
            ("Fed暗示今年降息三次 美股四大指數收紅", "聯準會主席鮑爾表示通膨已受控...", "CNBC"),
            ("NVIDIA推出新款AI晶片 股價與市值創新高", "NVIDIA GTC大會發布...", "Bloomberg"),
            ("蘋果放棄電動車計畫 轉向生成式AI", "據傳蘋果已取消長達十年的泰坦計畫...", "Reuters"),
        ]

        for title, content, source in us_news:
            FinancialNews.objects.get_or_create(
                title=title,
                defaults={
                    'category': us_cat,
                    'content': content,
                    'source': source,
                    'source_url': 'https://example.com',
                    'published_at': timezone.now()
                }
            )

        # 2. Create Daily Summaries
        DailyNewsSummary.objects.get_or_create(
            category=tw_cat,
            date=today,
            defaults={
                'summary': '今日台股受美股激勵表現強勁，半導體與AI族群領漲。傳產方面航運股表現不俗。',
                'conclusion': '大盤技術面轉強，外資回補，短線可留意AI伺服器供應鏈與高殖利率個股。',
                'news_count': 15
            }
        )
        
        DailyNewsSummary.objects.get_or_create(
            category=us_cat,
            date=today,
            defaults={
                'summary': '美股受Fed降息預期激勵全面上揚，科技股為領頭羊。通膨數據符合預期。',
                'conclusion': '市場氛圍樂觀，聚焦科技巨頭財報與AI發展。建議持續關注通膨數據變化。',
                'news_count': 12
            }
        )

        # 3. Create Stock Recommendations
        twse = StockMarket.objects.get(code='TWSE')
        tsmc, _ = StockRecommendation.objects.get_or_create(
            stock_code='2330',
            market=twse,
            recommendation_date=today,
            defaults={
                'stock_name': '台積電',
                'current_price': 780.00,
                'price_change': 15.00,
                'price_change_percent': 1.96,
                'recommendation_reason': '先進製程領先全球，AI晶片需求主要受惠者，營收展望佳。'
            }
        )
        StockTrend.objects.get_or_create(
            stock=tsmc,
            analysis_date=today,
            defaults={'trend_description': '技術面突破盤整區間，均線呈現多頭排列，外資持續買超，短線目標價看800元。'}
        )

        foxconn, _ = StockRecommendation.objects.get_or_create(
            stock_code='2317',
            market=twse,
            recommendation_date=today,
            defaults={
                'stock_name': '鴻海',
                'current_price': 105.50,
                'price_change': -0.50,
                'price_change_percent': -0.47,
                'recommendation_reason': 'AI伺服器市占率高，電動車佈局逐漸發酵，本益比偏低。'
            }
        )
        StockTrend.objects.get_or_create(
            stock=foxconn,
            analysis_date=today,
            defaults={'trend_description': '股價在年線附近震盪整理，下檔支撐強勁，等待量能放大攻擊。'}
        )

        nyse = StockMarket.objects.get(code='NYSE')
        nvda, _ = StockRecommendation.objects.get_or_create(
            stock_code='NVDA',
            market=nyse,
            recommendation_date=today,
            defaults={
                'stock_name': 'NVIDIA',
                'current_price': 890.00,
                'price_change': 25.40,
                'price_change_percent': 2.94,
                'recommendation_reason': 'GPU市場壟斷地位穩固，數據中心營收爆發性成長。'
            }
        )
        StockTrend.objects.get_or_create(
            stock=nvda,
            analysis_date=today,
            defaults={'trend_description': '股價沿五日線上攻，動能強勁，唯乖離率過大需留意短線震盪。'}
        )

        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
