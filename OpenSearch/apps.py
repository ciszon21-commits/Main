"""
OpenSearch App Configuration
"""
from django.apps import AppConfig


class OpenSearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'OpenSearch'
    verbose_name = 'OpenSearch 搜尋引擎'
