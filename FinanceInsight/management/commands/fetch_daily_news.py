from django.core.management.base import BaseCommand
from FinanceInsight.utils.news_fetcher import fetch_and_summarize_news

class Command(BaseCommand):
    help = 'Fetch daily financial news and generate summaries'

    def handle(self, *args, **options):
        self.stdout.write('Starting daily news fetch...')
        
        results = fetch_and_summarize_news()
        
        for category, count in results.items():
            self.stdout.write(self.style.SUCCESS(f'Category {category}: Fetched {count} news items'))
            
        self.stdout.write(self.style.SUCCESS('News fetch completed.'))
