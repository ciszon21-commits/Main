from django.apps import AppConfig


class PatentregistryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PatentRegistry'

    def ready(self):
        from SinoFile.registry import register_archivable_field
        from .models import GrantedPatent
        
        register_archivable_field(GrantedPatent, 'certificate')
