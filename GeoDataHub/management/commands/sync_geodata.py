from django.core.management.base import BaseCommand
from GeoDataHub.services import OpenSearchMappingService
import time

class Command(BaseCommand):
    help = '與 OpenSearch 同步地理資料 (兩階段模式)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='full',
            choices=['metadata', 'location', 'full'],
            help='同步模式: metadata (僅快擷資料), location (解析座標), full (兩階段並行)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='限制處理筆數 (0 表示不限)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='批次寫入量 (預設 100)'
        )

    def handle(self, *args, **options):
        mode = options['mode']
        limit = options['limit']
        batch_size = options['batch_size']

        self.stdout.write(self.style.SUCCESS(f'開始執行地理資料同步任務... 模式: {mode}'))
        
        service = OpenSearchMappingService()
        
        start_time = time.time()
        
        try:
            results = service.sync_sino_maps_two_stage(
                mode=mode,
                limit=limit,
                batch_size=batch_size
            )
            
            elapsed = time.time() - start_time
            
            self.stdout.write(self.style.SUCCESS('同步任務執行完畢！'))
            self.stdout.write(f'執行耗時: {elapsed:.2f} 秒')
            self.stdout.write(f'詳細結果: {results}')
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n任務被使用者中斷。請檢查「資料同步日誌」以確認最後進度。'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'發生嚴重錯誤: {str(e)}'))
