from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Setup initial groups and permissions for BudgetReview'

    def handle(self, *args, **kwargs):
        groups = ['Professional', 'Budget', 'Admin']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Group already exists: {group_name}'))

        # Add some basic permissions if needed in the future
        # For now, we mainly use these groups for role-based access control in views
