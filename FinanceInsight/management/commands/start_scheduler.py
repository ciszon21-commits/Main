from django.core.management.base import BaseCommand
from FinanceInsight.utils.stock_fetcher import update_all_stock_prices
import schedule
import time
import sys
from datetime import datetime

class Command(BaseCommand):
    help = 'Start background scheduler for stock updates'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting FinanceInsight Scheduler...'))
        self.stdout.write('Press Ctrl+C to stop.')

        # Schedule jobs
        # Run every 60 seconds for demo purposes (real world maybe 5-10 mins)
        schedule.every(60).seconds.do(self.run_update)
        
        # Also run immediately on start
        self.run_update()

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nScheduler stopped.'))
            sys.exit(0)

    def run_update(self):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.stdout.write(f"[{timestamp}] Running stock update...")
        try:
            results = update_all_stock_prices()
            success = results.get('success', 0)
            simulated = results.get('simulated', 0)
            failed = results.get('failed', 0)
            self.stdout.write(f"  > Update finished. Success: {success}, Simulated: {simulated}, Failed: {failed}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  > Error: {e}"))
