from django.core.management.base import BaseCommand
from GeoDataHub.services import OpenSearchMappingService

class Command(BaseCommand):
    help = 'Sync map data from OpenSearch to GeoDataHub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of documents to sync (ignored if --all is used)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync ALL documents from the index'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of documents per batch during sync'
        )
        parser.add_argument(
            '--index',
            type=str,
            default='sino_map',
            help='OpenSearch index to sync from'
        )

    def handle(self, *args, **options):
        limit = None if options['all'] else options['limit']
        batch_size = options['batch_size']
        index = options['index']
        
        mode = "ALL" if options['all'] else f"LIMIT {limit}"
        self.stdout.write(self.style.SUCCESS(f'Starting sync from OpenSearch index: {index} ({mode}, batch={batch_size})...'))
        
        service = OpenSearchMappingService()
        result = service.sync_sino_maps(limit=limit, batch_size=batch_size)
        
        if 'metadata_stage' in result:
            meta = result['metadata_stage']
            self.stdout.write(self.style.SUCCESS('Metadata Sync:'))
            self.stdout.write(f"  Processed: {meta.get('processed', 0)}")
            self.stdout.write(f"  Created: {meta.get('created', 0)}")
            if 'error' in meta:
                self.stdout.write(self.style.ERROR(f"  Error: {meta['error']}"))

        if 'location_stage' in result:
            loc = result['location_stage']
            self.stdout.write(self.style.SUCCESS('\nLocation Resolution:'))
            self.stdout.write(f"  Processed: {loc.get('processed', 0)}")
            self.stdout.write(f"  Updated: {loc.get('updated', 0)}")
            if 'error' in loc:
                self.stdout.write(self.style.ERROR(f"  Error: {loc['error']}"))
        
        self.stdout.write(self.style.SUCCESS('Sync completed successfully.'))
        if options['all']:
            self.stdout.write(self.style.WARNING('Note: Syncing all records may take time depending on the dataset size.'))
