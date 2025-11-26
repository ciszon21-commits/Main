from datetime import datetime, timedelta
from django.db.models import Q, F, Value
from django.db.models import QuerySet, CharField
from django.db.models import Case, When
from django.db.models import Subquery, OuterRef
from django import template

from PMIS import models as PMISModels
register = template.Library()



@register.simple_tag
def line_group_last_message_anno(qs:'QuerySet[PMISModels.LineGroupMapping]') -> 'QuerySet[PMISModels.LineGroupMapping]':
    if not qs: return qs
    lmOF = PMISModels.LineMessage.objects.filter(GroupId=OuterRef('Id'))
    lmOF = lmOF.annotate(
        text=Case(
            When(MsgText__isnull=False, then=F('MsgText')),
            When(ImageUID__isnull=False, then=Value('圖片')),
            When(FileUID__isnull=False, then=F('ExtName')+Value('檔案')),
            default=Value(''),
            output_field=CharField()
        ),
    )
    lmOF = lmOF.order_by('-CreateDate')
    lmTextSQ = Subquery(lmOF.values('text')[:1])
    qs = qs.annotate(
        last_message=lmTextSQ,
    )
    return qs
