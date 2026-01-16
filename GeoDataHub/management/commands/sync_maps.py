from django.core.management.base import BaseCommand
from GeoDataHub.services import OpenSearchMappingService

class Command(BaseCommand):
    help = 'Sync map data from OpenSearch to GeoDataHub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of documents to sync'
        )
        parser.add_argument(
            '--index',
            type=str,
            default='sino_map',
            help='OpenSearch index to sync from'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        index = options['index']
        
        self.stdout.write(self.style.SUCCESS(f'Starting sync from OpenSearch index: {index}...'))
        
        service = OpenSearchMappingService()
        result = service.sync_sino_maps(limit=limit)
        
        self.stdout.write(f"Total found: {result['total_found']}")
        self.stdout.write(f"New created: {result['new_created']}")
        self.stdout.write(self.style.SUCCESS(f"Location synced: {result['location_synced']}"))
        
        self.stdout.write(self.style.SUCCESS('Sync completed successfully.'))
