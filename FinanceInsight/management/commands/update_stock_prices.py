from django.core.management.base import BaseCommand
from FinanceInsight.utils.stock_fetcher import update_all_stock_prices

class Command(BaseCommand):
    help = 'Update stock prices from Yahoo Finance'

    def handle(self, *args, **options):
        self.stdout.write('Starting stock price update...')
        
        results = update_all_stock_prices()
        
        self.stdout.write(self.style.SUCCESS(
            f"Update complete. Success: {results['success']}, Failed: {results['failed']}"
        ))
