from django.conf import settings

# from PMIS import models as PmisModels

import os

class ArchiveFolder:
    def get_file_paths(self):
        files = self.filesInFolder.all()
        paths = files.values_list('file', flat=True)
        return paths
    def get_dynamic_size(self):
        sizes = 0
        for file in self.filesInFolder.all():
            size = file.get_dynamic_size()
            sizes += size
        return sizes
    def get_file_details(self):
        detail = {}
        for file in self.filesInFolder.all():
            uuid = str(file.UUID)
            detail[uuid] = file.get_detail()
        return detail
    def get_detail(self):
        detail = self.get_file_details()
        sizes = list(map(lambda i: i[1].get('size'), detail.items()))
        exist = [v.get('path') for k, v in detail.items() if v.get('exist')]
        none = [v.get('path') for k, v in detail.items() if not v.get('exist')]
        return {
            'count': len(detail),
            'exist': exist,
            'none': none,
            'size': sum(sizes),
        }
    def has_archive_srote(self):
        filter = {'ArchiveID': self.folderName}
        asp = PmisModels.DocCollab_ArchiveStorePath.objects.filter(**filter).first()
        return True if asp else False
    def remove_file(self):
        if not self.has_archive_srote(): return {'message': 'noArchiveStore'}
        for file in self.filesInFolder.all():
            file.remove_file()
        self.has_files = False
        self.save()
        return {'message': 'success'}
    def check_this(self):
        detail = self.get_detail()
        self.set_has_files(detail)
        return detail
    def set_has_files(self, detail={}):
        detail = detail if detail else self.get_detail()
        exist = detail.get('exist', [])
        self.has_files = len(exist) != 0
        self.save()


class ArchiveFile:
    def get_detail(self):
        detail = {
            'path': self.full_path,
            'exist': self.is_file_exist(),
            'size': self.get_dynamic_size(),
        }
        return detail
    def is_file_exist(self):
        return os.path.isfile(self.full_path)
    def get_dynamic_size(self):
        if not self.is_file_exist(): return 0
        return os.path.getsize(self.full_path)
    def remove_file(self):
        if not self.is_file_exist(): return
        os.remove(self.full_path)
    def full_path(self):
        return os.path.join(settings.MEDIA_DIR, self.file)
