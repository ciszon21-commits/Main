from datetime import datetime
from typing import (
    Iterable,
    TypedDict,
    TYPE_CHECKING,
)
import os

from django.utils import timezone

if TYPE_CHECKING:
    from CommonUse.models import ArchiveStorePath

from SinoExtension.tools import attribute_func

from StudioBase.services.mixins import CommonUseCatcherMixin

from SinoArchive.types import (
    ArchiveFolderDetail,
    ArchiveFileDetail,
)
from SinoArchive.constants import (
    ARCHIVE_SIZE,
    ARCHIVE_DIR,
)
from SinoArchive.models import (
    ArchiveFolder,
    ArchiveFile,
)
from .mixins import SinoArchiveCatcherMixin
from .methods import get_folder




class WorkResponse(TypedDict):
    message: 'str'


class ArchiveFolderProcessor(
        CommonUseCatcherMixin,
        SinoArchiveCatcherMixin,
    ):
    def __init__(self, folder:'ArchiveFolder'):
        self.folder = folder


    def get_archive_store_paths(self):
        if not self.archive_sp_manager:
            return []
        return self.archive_sp_manager.filter(ArchiveID=self.folder.folder_name)

    def get_archive_folders(self):
        return [self.folder]
    def get_archive_files(self):
        return self.folder.files_in_folders.all()


    @property
    def archive_store_path(self) -> 'ArchiveStorePath|None':
        if not self.archive_sp_list:
            return None
        return self.archive_sp_list[0]


    @property
    def folder_name(self) -> 'str':
        return self.folder.folder_name
    @property
    def total_size(self) -> 'int':
        return self.folder.total_size
    @property
    def fulled(self) -> 'bool':
        return self.folder.fulled
    @property
    def fulled_at(self) -> 'datetime':
        return self.folder.fulled_at
    @property
    def create_at(self) -> 'datetime':
        return self.folder.create_at
    @property
    def has_files(self) -> 'bool':
        return self.folder.has_files



    @property
    def archive_path(self) -> 'str':
        return os.path.join(ARCHIVE_DIR, self.folder_name)



    def get_file_paths(self) -> 'Iterable[str]':
        return list(map(attribute_func('file'), self.archive_file_list))
    def get_dynamic_size(self) -> 'int':
        if not self.archive_file_list:
            return 0
        return sum(map(attribute_func('get_dynamic_size'), self.archive_file_list))
    def get_file_details(self) -> 'dict[str,ArchiveFileDetail]':
        def wrap(file:'ArchiveFile') -> 'tuple[str,ArchiveFileDetail]':
            uuid = str(file.UUID)
            detail = file.get_detail()
            return (uuid, detail)
        return dict(map(wrap, self.archive_file_list))

    def get_detail(self) -> 'ArchiveFolderDetail':
        detail = self.get_file_details()
        sizes = list(map(attribute_func('size'), detail.values()))
        exist = [v.get('path') for k, v in detail.items() if v.get('exist')]
        none = [v.get('path') for k, v in detail.items() if not v.get('exist')]
        return {
            'count': len(detail),
            'exist': exist,
            'none': none,
            'size': sum(sizes),
        }

    def has_archive_srote(self) -> 'bool':
        return bool(self.archive_store_path)

    def remove_file(self) -> 'WorkResponse':
        if not self.archive_store_path:
            return {'message': 'noArchiveStore'}
        for file in self.archive_file_list:
            file.remove_file()
        self.folder.has_files = False
        self.folder.save()
        return {'message': 'success'}


    def set_has_files(self, detail:'ArchiveFolderDetail'={}):
        detail = detail or self.get_detail()
        exist = detail.get('exist', [])
        self.folder.has_files = len(exist) != 0
        self.folder.save()

    def check_this(self) -> 'ArchiveFolderDetail':
        detail = self.get_detail()
        self.set_has_files(detail)
        return detail

    def full(self):
        self.folder.fulled = True
        self.folder.fulled_at = timezone.now()
        self.folder.save()

    def add_size(self, size:'int'):
        self.folder.total_size += size
        self.folder.save()





    @classmethod
    def final_folder(cls, size:'int'=None) -> 'ArchiveFolderProcessor':
        """ 抓取最後一個未滿的 備份資料夾。
        如果加上 size 會滿的話，就把原本的資料夾設置為已滿，並另外開一個新的資料夾。
        """
        final_folder = ArchiveFolderProcessor(get_folder())
        if size is None:
            return final_folder
        if final_folder.total_size + size > ARCHIVE_SIZE:
            final_folder.full()
        return ArchiveFolderProcessor(get_folder())




