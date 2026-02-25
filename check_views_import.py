import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

try:
    from EngineerRPG import views
    print("Successfully imported EngineerRPG.views")
except Exception as e:
    print(f"Failed to import EngineerRPG.views: {e}")
    import traceback
    traceback.print_exc()
