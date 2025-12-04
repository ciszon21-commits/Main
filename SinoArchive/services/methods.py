import os

from SinoArchive.constants import (
    MEDIA_DIR,
    ARCHIVE_DIR,
)
from SinoArchive.models import (
    ArchiveFolder,
    ArchiveFile,
)


def get_folder():
    a_fol = ArchiveFolder.objects.filter(fulled=False).first()
    if a_fol:
        return a_fol
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    n_folder = ArchiveFolder()
    n_folder.save()
    folder = os.path.join(ARCHIVE_DIR, str(n_folder))
    if not os.path.exists(folder):
        os.makedirs(folder)
    return n_folder


# filename 不包含 /media/
def add_or_update_archive(filename:'str'):
    if not ArchiveFile.objects.filter(file=filename).exists():
        add_archive(filename)
    else:
        # 好像沒有需要update的動作
        pass


def add_archive(filename:'str'):
    af = ArchiveFile()
    af.file = filename
    base, extension = os.path.splitext(filename)
    # re.compile(r'[^\\]*\.(\w+)$').match(filename).group(1)
    af.ext = extension
    full_path = os.path.join(MEDIA_DIR, filename)
    af.size = os.stat(full_path).st_size
    af.save()


