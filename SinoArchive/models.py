import os
import shutil
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from StudioBase.utils import File
from . import model_managers as managers
from . import model_methods as methods

from SinoArchive.constants import (
    MEDIA_DIR,
    ARCHIVE_DIR,
    BACKUP_DIR,
    AUTO_ARCHIVE,
    ARCHIVE_SIZE,
)



# filename 不包含 /media/
def addOrUpdateArchive(filename):
    if ArchiveFile.objects.filter(file=filename).count() == 0:
        addArchive(filename)
    else:
        # 好像沒有需要update的動作
        pass

def addArchive(filename):
    af = ArchiveFile()
    af.file = filename
    base, extension = os.path.splitext(filename)
    # re.compile(r'[^\\]*\.(\w+)$').match(filename).group(1)
    af.ext = extension
    full_path = os.path.join(MEDIA_DIR,filename)
    af.size = os.stat(full_path).st_size
    af.save()

def get_folder():
    f = ArchiveFolder.objects.filter(fulled=False)
    if len(f) == 0 :
        if not os.path.exists(ARCHIVE_DIR):
            os.makedirs(ARCHIVE_DIR)
        newFolder = ArchiveFolder()
        newFolder.save()
        folder = os.path.join(ARCHIVE_DIR, str(newFolder))
        if not os.path.exists(folder):
            os.makedirs(folder)
        return newFolder
    else :
        return f[0]

class ArchiveFolder(models.Model):
    folderName = models.CharField(null=True, blank=True,max_length=255, verbose_name= _('資料夾名稱'))
    totalSize = models.BigIntegerField(default=0,verbose_name= _('總容量'))
    fulled = models.BooleanField(default=False,verbose_name= _('已滿'))
    fulled_at = models.DateTimeField(null=True, blank=True)
    create_at = models.DateTimeField(null=True, blank=True)
    has_files = models.BooleanField(default=True, verbose_name='還有檔案')
    def __str__(self):
        return self.folderName
    def check_this(self, *args, **kwargs): return methods.ArchiveFolder.check_this(self, *args, **kwargs)
    def get_detail(self, *args, **kwargs): return methods.ArchiveFolder.get_detail(self, *args, **kwargs)
    def get_dynamic_size(self, *args, **kwargs): return methods.ArchiveFolder.get_dynamic_size(self, *args, **kwargs)
    def get_file_paths(self, *args, **kwargs): return methods.ArchiveFolder.get_file_paths(self, *args, **kwargs)
    def get_file_details(self, *args, **kwargs): return methods.ArchiveFolder.get_file_details(self, *args, **kwargs)
    def has_archive_srote(self, *args, **kwargs): return methods.ArchiveFolder.has_archive_srote(self, *args, **kwargs)
    def remove_file(self, *args, **kwargs): return methods.ArchiveFolder.remove_file(self, *args, **kwargs)
    def set_has_files(self, *args, **kwargs): return methods.ArchiveFolder.set_has_files(self, *args, **kwargs)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.folderName:
            self.folderName = "BIM"+str(self.id).zfill(5)
            self.create_at = timezone.now()
            self.save()
    def full(self):
        self.fulled = True
        self.fulled_at = timezone.now()
        self.save()
    def addSize(self,fSize):
        self.totalSize += fSize
        self.save()

class ArchiveFile(models.Model):
    UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.CharField(max_length=500, verbose_name= _('原始路徑'))
    ext = models.CharField(max_length=255, verbose_name= _('副檔名'))
    size = models.BigIntegerField(verbose_name=_('容量'))
    folder = models.ForeignKey(ArchiveFolder, related_name='filesInFolder', verbose_name= _('典藏資料夾'),on_delete=models.CASCADE,null=True, blank=True)
    processed = models.BooleanField(default=False,verbose_name= _('已處理'))
    uploaded_at = models.DateTimeField(auto_now_add=True)
    process_at = models.DateTimeField(null=True, blank=True)
    objects = managers.ArchiveFile()
    def get_detail(self, *args, **kwargs): return methods.ArchiveFile.get_detail(self, *args, **kwargs)
    def get_dynamic_size(self, *args, **kwargs): return methods.ArchiveFile.get_dynamic_size(self, *args, **kwargs)
    def is_file_exist(self, *args, **kwargs): return methods.ArchiveFile.is_file_exist(self, *args, **kwargs)
    def remove_file(self, *args, **kwargs): return methods.ArchiveFile.remove_file(self, *args, **kwargs)
    @property
    def full_path(self, *args, **kwargs): return methods.ArchiveFile.full_path(self, *args, **kwargs)
    def __str__(self):
        return self.file
    def get_full_path(self):
        return os.path.join(str(self.folder), f"{self.UUID}{self.ext}")
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if AUTO_ARCHIVE:
            self.archiveThis()
    def get_archive_name(self):
        return str(self.UUID)+self.ext
    def get_backup_file(self):
        return os.path.join(BACKUP_DIR, str(self.folder), f"{self.UUID}{self.ext}")
    def archiveThis(self):
        if not self.processed:
            final_folder = get_folder()
            if final_folder.totalSize + self.size > ARCHIVE_SIZE:
                final_folder.full()
                final_folder = get_folder()
            self.folder = final_folder
            from_path = os.path.join(MEDIA_DIR,self.file)
            if os.path.exists(from_path):
                to_folder = os.path.join(ARCHIVE_DIR,str(final_folder))
                to_path = os.path.join(to_folder,self.get_archive_name())
                shutil.copy(from_path,to_path)
                self.process_at = timezone.now()
                self.processed = True
                final_folder.addSize(self.size)
                archiveLog = os.path.join(to_folder,"_"+str(final_folder)+".txt")
                sizeStr = File.size_format(self.size)
                f = open(archiveLog,'a+',encoding = 'utf-8')
                f.write(self.get_archive_name()+"\t"+self.uploaded_at.strftime("%Y/%m/%d %H:%M:%S")+"\t"+sizeStr+"\t"+str(self.file)+"\n")
                f.close()
            else:
                print(from_path + "不存在")
            self.save()
