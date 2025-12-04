from functools import cached_property
from typing import Iterable

from django.db.models import Manager

from SinoExtension.tools import SearchList

from SinoArchive.models import (
    ArchiveFolder,
    ArchiveFile,
)




class SinoArchiveCatcherMixin:
    archive_folder_manager:'Manager[ArchiveFolder]' = ArchiveFolder.objects
    archive_file_manager:'Manager[ArchiveFile]' = ArchiveFile.objects.select_related('folder')



    def get_archive_folders(self) -> 'Iterable[ArchiveFolder]':
        return self.archive_folder_manager.none()
    def get_archive_files(self) -> 'Iterable[ArchiveFile]':
        return self.archive_file_manager.none()


    @cached_property
    def archive_folder_list(self) -> 'SearchList[ArchiveFolder]':
        return SearchList(self.get_archive_folders())
    @cached_property
    def archive_file_list(self) -> 'SearchList[ArchiveFile]':
        return SearchList(self.get_archive_files())


