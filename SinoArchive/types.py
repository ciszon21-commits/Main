from typing import (
    Literal,
    TypedDict,
)



class ArchiveFolderDetail(TypedDict):
    count: 'int'
    exist: 'list[str]'
    none: 'list[str]'
    size: 'int'

class ArchiveFileDetail(TypedDict):
    path: 'str'
    exist: 'bool'
    size: 'int'




ArchiveCate = Literal[
    'Folder',
    'File',
]

