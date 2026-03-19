from django.core.management.base import BaseCommand
from django.db.models import Sum
from XrResource.models import XrEquipment, XrBulkItem, XrRentalRecord, XrRentalBulkItem

class Command(BaseCommand):
    help = 'Synchronizes and fixes inventory counts and equipment statuses based on rental records'

    def handle(self, *args, **options):
        self.stdout.write('Starting inventory synchronization...')

        # 1. Reset Bulk Item Counts
        self.stdout.write('Checking Bulk Items...')
        for item in XrBulkItem.objects.all():
            # Pending status sum
            pending_count = XrRentalBulkItem.objects.filter(
                bulk_item=item,
                rental_record__status='pending'
            ).aggregate(Sum('count'))['count__sum'] or 0
            
            # Currently out (Approved but not returned)
            out_count = XrRentalBulkItem.objects.filter(
                bulk_item=item,
                rental_record__status='approved',
                is_returned=False
            ).aggregate(Sum('count'))['count__sum'] or 0
            
            # Update counts
            item.reserved_count = pending_count
            item.available_count = item.total_count - out_count
            # We bypass the custom save() to avoid diff calculation during sync
            # or we just set it and save normally if our save handles it
            # But wait, our custom save() calculates DIFF from DB. 
            # It's safer to use update() or just save manually if we know the values are absolute.
            
            # Actually, my custom save calculates DIFF of TOTAL_COUNT.
            # If I only change reserved/available, it won't trigger the DIFF logic.
            item.save()
            self.stdout.write(f'  - {item.name}: Available={item.available_count}/{item.total_count}, Reserved={item.reserved_count}')

        # 2. Sync Equipment Statuses
        self.stdout.write('Checking Individual Equipments...')
        # Reset all reserved/rented back to available first (if not maintenance/retired)
        XrEquipment.objects.filter(status__in=['reserved', 'rented']).update(status='available')
        
        # Mark Reserved
        pending_rentals = XrRentalRecord.objects.filter(status='pending')
        for rental in pending_rentals:
            rental.equipments.all().update(status='reserved')
            
        # Mark Rented
        approved_rentals = XrRentalRecord.objects.filter(status='approved')
        for rental in approved_rentals:
            # Only equipment not yet returned. 
            # Note: We don't have per-equipment 'is_returned' yet, only per bulk item.
            # But the logic is: if record is 'approved', it's 'rented'. 
            # If it were 'returned', the record status would be 'returned'.
            rental.equipments.all().update(status='rented')

        self.stdout.write(self.style.SUCCESS('Inventory synchronization complete!'))
