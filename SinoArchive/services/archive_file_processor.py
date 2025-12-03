from datetime import datetime
import os
import shutil

from django.utils import timezone

from SinoExtension.tools import size_format

from SinoArchive.types import ArchiveFileDetail
from SinoArchive.constants import (
    MEDIA_DIR,
    BACKUP_DIR,
)
from SinoArchive.models import (
    ArchiveFolder,
    ArchiveFile,
)

from .archive_folder_processor import ArchiveFolderProcessor



class ArchiveFileProcessor:
    def __init__(self, file:'ArchiveFile'):
        self.a_file = file




    @property
    def file(self) -> 'str':
        return self.a_file.file
    @property
    def ext(self) -> 'str':
        return self.a_file.ext
    @property
    def size(self) -> 'int':
        return self.a_file.size
    @property
    def folder(self) -> 'ArchiveFolder':
        return self.a_file.folder
    @property
    def processed(self) -> 'bool':
        return self.a_file.processed
    @property
    def uploaded_at(self) -> 'datetime':
        return self.a_file.uploaded_at
    @property
    def process_at(self) -> 'datetime':
        return self.a_file.process_at



    @property
    def full_path(self):
        return os.path.join(MEDIA_DIR, self.a_file.file)
    @property
    def archive_path(self):
        return os.path.join(self.folder.folder_name, f"{self.a_file.pk}{self.a_file.ext}")


    def get_detail(self) -> 'ArchiveFileDetail':
        detail = {
            'path': self.full_path,
            'exist': self.is_file_exist(),
            'size': self.get_dynamic_size(),
        }
        return detail

    def is_file_exist(self) -> 'bool':
        return os.path.isfile(self.full_path)
    def get_dynamic_size(self) -> 'int':
        if not self.is_file_exist(): return 0
        return os.path.getsize(self.full_path)
    def remove_file(self):
        if not self.is_file_exist(): return
        os.remove(self.full_path)

    def get_archive_name(self) -> 'str':
        return f"{self.a_file.pk}{self.a_file.ext}"
    def get_backup_file(self) -> 'str':
        return os.path.join(BACKUP_DIR, self.folder.folder_name, f"{self.a_file.pk}{self.a_file.ext}")



    def archive_this(self):
        if self.a_file.processed:
            return
        final_folder = ArchiveFolderProcessor.final_folder()
        self.a_file.folder = final_folder.folder
        from_path = self.full_path
        if not os.path.exists(from_path):
            print(f"{self.full_path} 不存在")
        else:
            to_folder = final_folder.archive_path
            to_path = os.path.join(to_folder, self.get_archive_name())
            shutil.copy(from_path, to_path)
            self.a_file.process_at = timezone.now()
            self.a_file.processed = True
            final_folder.add_size(self.a_file.size)
            archiveLog = os.path.join(to_folder, f"_{final_folder.folder_name}.txt")
            size_str = size_format(self.size)
            with open(archiveLog, 'a+', encoding='utf-8') as f:
                f.write(self.get_archive_name()+"\t"+self.uploaded_at.strftime("%Y/%m/%d %H:%M:%S")+"\t"+size_str+"\t"+str(self.a_file.file)+"\n")
        self.a_file.save()


