from django.apps import AppConfig


class EVCodeSigningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'EVCodeSigning'
    verbose_name = 'EV Code Signing 簽章管理'

    def ready(self):
        from SinoFile.registry import register_archivable_field
        from .models import SigningFile
        
        register_archivable_field(SigningFile, 'original_file')
        register_archivable_field(SigningFile, 'signed_file')
