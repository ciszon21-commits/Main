import os
import uuid

from django.db import models
from django.db.models import Manager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import model_managers as managers

from SinoArchive.constants import (
    MEDIA_DIR,
    AUTO_ARCHIVE,
)




class ArchiveFolder(models.Model):
    folder_name = models.CharField(null=True, blank=True,max_length=255, verbose_name=_('資料夾名稱'))
    total_size = models.BigIntegerField(default=0, verbose_name=_('總容量'))
    fulled = models.BooleanField(default=False, verbose_name=_('已滿'))
    fulled_at = models.DateTimeField(null=True, blank=True)
    create_at = models.DateTimeField(null=True, blank=True)
    has_files = models.BooleanField(default=True, verbose_name=_('還有檔案'))

    files_in_folders: 'Manager[ArchiveFile]'

    def __str__(self):
        return self.folder_name
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.folder_name: return
        self.folder_name = "BIM"+str(self.pk).zfill(5)
        self.create_at = timezone.now()
        self.save()



class ArchiveFile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.CharField(max_length=500, verbose_name=_('原始路徑'))
    ext = models.CharField(max_length=255, verbose_name=_('副檔名'))
    size = models.BigIntegerField(verbose_name=_('容量'))
    folder = models.ForeignKey(ArchiveFolder, related_name='files_in_folders', verbose_name=_('典藏資料夾'),on_delete=models.CASCADE,null=True, blank=True)
    processed = models.BooleanField(default=False,verbose_name=_('已處理'))
    uploaded_at = models.DateTimeField(auto_now_add=True)
    process_at = models.DateTimeField(null=True, blank=True)

    objects = managers.ArchiveFile()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if AUTO_ARCHIVE:
            # TODO 想一下，這個要怎麼改
            self.archive_this()

    def __str__(self):
        return self.file

    @property
    def full_path(self):
        return os.path.join(MEDIA_DIR, self.file)


