from django.conf import settings


MEDIA_DIR = getattr(settings, 'MEDIA_DIR', None)

BACKUP_DIR = getattr(settings, 'BACKUP_DIR', None)
AUTO_ARCHIVE = getattr(settings, 'AUTO_ARCHIVE', False)

ARCHIVE_DIR = getattr(settings, 'ARCHIVE_DIR', None)
ARCHIVE_SIZE = getattr(settings, 'ARCHIVE_SIZE', 1000000000)

