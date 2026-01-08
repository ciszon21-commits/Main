from django.apps import AppConfig


class TeamKnowledgeHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TeamKnowledgeHub'
    verbose_name = '團隊知識管理'

    def ready(self):
        from SinoFile.registry import register_archivable_field
        from .models import ItemAttachment, CommentAttachment
        
        register_archivable_field(ItemAttachment, 'file')
        register_archivable_field(CommentAttachment, 'file')
