from django import template
from django.db.models import F
from django.db.models import Case, Count, Value, When
from django.db.models import CharField
from django.db.models.functions import Concat
from django.db.models.functions import TruncDate
from django.db.models.functions.datetime import ExtractMonth, ExtractYear

register = template.Library()

@register.filter
def date_used(qs):
    if not qs: return []
    # 按時間分割
    qs = qs.annotate(date=TruncDate('time'))
    qs = qs.values('date')
    # 補上需要的 annotate 內容
    qs = qs.annotate(count=Count('id'))
    qs = qs.annotate(visits=Count('user_id', distinct=True))
    qs = qs.values('date', 'count', 'visits')
    return qs
