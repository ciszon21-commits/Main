import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import AdminWhitelist

try:
    count = AdminWhitelist.objects.count()
    print(f"Successfully accessed DB. AdminWhitelist count: {count}")
except Exception as e:
    print(f"Failed to access DB: {e}")
