from django.apps import AppConfig


class ClashclassifierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ClashClassifier'

    def ready(self):
        from SinoFile.registry import register_archivable_field
        from .models import MLModel, ClashReport

        # ML model是特殊用法，應該要排除        
        # register_archivable_field(MLModel, 'file')
        register_archivable_field(ClashReport, 'html_file')
        register_archivable_field(ClashReport, 'csv_file')
