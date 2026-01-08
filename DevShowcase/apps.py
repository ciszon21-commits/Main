from django.apps import AppConfig


class DevshowcaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DevShowcase'
    verbose_name = '開發成果展示'

    def ready(self):
        from SinoFile.registry import register_archivable_field
        from .models import Achievement
        
        register_archivable_field(Achievement, 'video')
