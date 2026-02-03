from django.core.management.base import BaseCommand
from FinanceInsight.models import NewsCategory, StockMarket

class Command(BaseCommand):
    help = 'Initialize default data for FinanceInsight app'

    def handle(self, *args, **options):
        self.stdout.write('Initializing FinanceInsight data...')

        # Initialize News Categories
        categories = [
            ('TW_FINANCE', '台灣財經', '台灣股市、金融相關新聞'),
            ('US_FINANCE', '美國財經', '美股、聯準會、國際金融新聞'),
            ('INDUSTRY', '產業動態', '各類產業趨勢與發展'),
            ('GLOBAL', '國際經濟', '全球經濟局勢與重大事件'),
        ]

        for code, name, desc in categories:
            obj, created = NewsCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))
            else:
                self.stdout.write(f'Category already exists: {name}')

        # Initialize Stock Markets
        markets = [
            ('TWSE', '台北股市', '台灣', '台灣證券交易所'),
            ('NYSE', '紐約證券交易所', '美國', '全球市值最大的證券交易所'),
            ('NASDAQ', '那斯達克', '美國', '以前瞻性科技股為主的交易所'),
        ]

        for code, name, country, desc in markets:
            obj, created = StockMarket.objects.get_or_create(
                code=code,
                defaults={'name': name, 'country': country, 'description': desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created market: {name}'))
            else:
                self.stdout.write(f'Market already exists: {name}')

        self.stdout.write(self.style.SUCCESS('Initialization complete!'))
