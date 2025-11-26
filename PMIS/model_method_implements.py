import os
import re

from django.conf import settings

from . import models

# DocCollab_DBStorePath
def formatConnectionString(
        self:'models.DocCollab_DBStorePath'
    ) -> dict:
    css = self.ConnectionString.split(';')
    css = [c.split('=') for c in css]
    css = [[c.strip() for c in cc] for cc in css]
    return {c[0]: c[1] for c in css}

def getArchiveLineMessageFilePath(
        self: 'models.LineMessage',
        filename: 'str',
    ) -> str:
    bFile = self.get_base_file()
    if not bFile: return None
    docASP = models.DocCollab_ArchiveStorePath.objects.filter(ArchiveID=bFile.SourceArchive).first()
    if not docASP: return None
    dirpath = docASP.Path
    archiveId = docASP.ArchiveID
    path = os.path.join(dirpath, archiveId, filename)
    path = re.sub(r'\s', '', path)
    if not os.path.isfile(path): return ''
    return path
