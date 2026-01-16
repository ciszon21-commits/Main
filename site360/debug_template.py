import os
import django
from django.template.loader import get_template
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

try:
    t = get_template('site360/project_list.html')
    print("Found template:", t.origin.name)
except Exception as e:
    print("Error:", e)
    # Print search paths
    # from django.template.utils import get_app_template_dirs
    # print("Search paths:", get_app_template_dirs('templates'))
