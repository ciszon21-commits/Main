from functools import cached_property
from typing import (
    Iterable,
    TYPE_CHECKING,
)

from django.db.models import Manager

from SinoExtension.tools import (
    SearchList,
    is_app_ready,
)
if TYPE_CHECKING:
    from CommonUse.models import ArchiveStorePath



class CommonUseCatcherMixin:
    """ CommonUse 的中介層，
    避免沒有權限的專案直接呼叫 CommonUse 的 Model
    """
    @property
    def archive_sp_manager(self) -> 'Manager[ArchiveStorePath]':
        if not is_app_ready('CommonUse'):
            return None
        from CommonUse.models import ArchiveStorePath
        return ArchiveStorePath.objects



    def get_archive_store_paths(self) -> 'Iterable[ArchiveStorePath]':
        if not self.archive_sp_manager:
            return []
        return self.archive_sp_manager.none()



    @cached_property
    def archive_sp_list(self) -> 'SearchList[ArchiveStorePath]':
        return SearchList(self.get_archive_store_paths())


