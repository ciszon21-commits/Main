from django.db import models as DjModels

from . import models

class DocCollab_DBStorePath(DjModels.Manager):
    def get_home(self, projNo):
        dFilter = {'EntryName__icontains': projNo,}
        dbPath = models.DocCollab_DBStorePath.objects.filter(**dFilter).first()
        if not dbPath: return ''
        return dbPath.HomePage.replace(' ', '')
    def get_url(self, projNo):
        home = self.get_home(projNo)
        return f'{home}/BaseApp/Redirect.aspx?redirect='

class LineGroupMapping(DjModels.Manager):
    def space_comment(self):
        return models.LineGroupMapping(
            Id='comment',
            Name='留言板',
            Project='',
        )