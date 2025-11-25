from django.contrib.auth.models import User
from django.db import models as DjModels
from django.db.models import QuerySet

from .. import models


class GroupManager(DjModels.Manager):
    def get_joined_groups(cls:'GroupManager', user:'User') -> 'QuerySet[models.Group]':
        return models.Group.objects.filter(member_links__user=user).distinct()



