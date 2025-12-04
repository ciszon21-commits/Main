from datetime import datetime
import os
import re
import shutil
from typing import TYPE_CHECKING
from uuid import UUID

from django.utils import timezone
from django.db.models import Q

from SinoExtension.tools import (
    size_format,
    set_file_local_path,
)

if TYPE_CHECKING:
    from CommonUse.models import ArchiveStorePath

from StudioBase.services.mixins import CommonUseCatcherMixin
from SinoArchive.types import ArchiveFileDetail
from SinoArchive.constants import (
    ARCHIVE_DIR,
    BACKUP_DIR,
    MEDIA_DIR,
)
from SinoArchive.utils import normalize_cross_platform_path
from SinoArchive.models import (
    ArchiveFolder,
    ArchiveFile,
)

from .archive_folder_processor import ArchiveFolderProcessor





class ArchiveFileProcessor(
        CommonUseCatcherMixin,
    ):
    def __init__(self, file:'ArchiveFile'):
        self.a_file = file


    @property
    def uuid(self) -> 'UUID':
        return self.a_file.uuid
    @property
    def pk(self) -> 'UUID':
        return self.a_file.pk
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



    def get_archive_store_paths(self):
        if not self.archive_sp_manager:
            return []
        return self.archive_sp_manager.filter(ArchiveID=self.folder.folder_name)

    @property
    def archive_store_path(self) -> 'ArchiveStorePath|None':
        if not self.archive_sp_list:
            return None
        return self.archive_sp_list[0]



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






    @classmethod
    def get_archive_path(cls, path:'str') -> 'str':
        af_pro = cls.catch_archive_file_processor(path)
        if (
            not af_pro
            or not af_pro.archive_store_path
        ):
            return ''
        full_path = os.path.join(
            re.sub(r'\s+', '', af_pro.archive_store_path.Path),
            af_pro.folder.folder_name,
            f"{af_pro.a_file.pk}{af_pro.ext}"
        )
        return normalize_cross_platform_path(full_path)
    @classmethod
    def get_temp_path(cls, path:'str') -> 'str':
        af_pro = cls.catch_archive_file_processor(path)
        if (
            not af_pro
            or not af_pro.archive_store_path
        ):
            return ''
        full_path = os.path.join(
            ARCHIVE_DIR,
            af_pro.folder.folder_name,
            f"{af_pro.a_file.pk}{af_pro.ext}"
        )
        return normalize_cross_platform_path(full_path)
        # return os.path.normpath(full_path)


    @classmethod
    def catch_archive_file(cls, path:'str') -> 'ArchiveFile|None':
        path = set_file_local_path(path)
        norm_path = os.path.normpath(path)  # 統一格式
        s_path = norm_path.replace('\\', '/')
        b_path = norm_path.replace('/', '\\')
        aQ = Q(file=s_path) | Q(file=b_path)
        return ArchiveFile.objects.filter(aQ).first()
    @classmethod
    def catch_archive_file_processor(cls, path:'str') -> 'ArchiveFileProcessor|None':
        a_file = cls.catch_archive_file(path)
        if not a_file: return None
        return ArchiveFileProcessor(a_file)




