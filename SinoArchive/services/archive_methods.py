from SinoArchive.models import ArchiveFile

from .archive_file_processor import ArchiveFileProcessor



def get_archive_path(path:'str') -> 'str':
    return ArchiveFileProcessor.get_archive_path(path)
def get_temp_path(path:'str') -> 'str':
    return ArchiveFileProcessor.get_temp_path(path)

def catch_archive_file(path:'str') -> 'ArchiveFile|None':
    return ArchiveFileProcessor.catch_archive_file(path)
def catch_archive_file_processor(path:'str') -> 'ArchiveFileProcessor|None':
    return ArchiveFileProcessor.catch_archive_file_processor(path)

