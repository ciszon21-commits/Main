from django.apps import AppConfig


class CourseregistrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'CourseRegistration'

    def ready(self):
        from SinoFile.registry import register_archivable_field
        from .models import Course
        
        register_archivable_field(Course, 'pdf_file')
