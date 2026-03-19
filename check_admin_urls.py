import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()
from django.apps import apps
for app in apps.get_app_configs():
    if 'XrResource' in app.name or 'xrresource' in app.name.lower():
        print(f"App name: {app.name}, label: {app.label}")
        for model in app.get_models():
            print(f"  Model name: {model._meta.model_name}")
