from datetime import datetime, timedelta

from django import template
from django.db.models import Model
from django.db.models import Case, When
from django.db.models import Value as V
from django.db.models import Q
from django.db.models import QuerySet
from django.utils import timezone

# from Extension import MyTime

register = template.Library()


def getPattenData(patten):
    patten = patten.split('=')
    if patten[1].lower() == 'true':
        patten[1] = True
    elif patten[1].lower() == 'false':
        patten[1] = False
    elif patten[1].lower() == 'none':
        patten[1] = None
    return (patten[0], patten[1])

def getPattens(pattens):
    result = {}
    for patten in pattens.split(','):
        if '=' not in patten: continue
        pKey, pValue = getPattenData(patten)
        result[pKey] = pValue
    return result

def unzipList(items:'list[list[object]]') -> 'list[object]':
    return [i for ii in items for i in ii]


@register.filter
def to_query_set(items:'list[Model]') -> 'QuerySet[Model]':
    if isinstance(items, QuerySet): return items
    if not items: return items
    ids = list(map(lambda i: i.pk, items))
    return type(items[0]).objects.filter(pk__in=ids)

@register.filter
def filter(qs, pattens):
    if not qs or not pattens: return qs
    pattens = getPattens(pattens)
    return qs.filter(**pattens)

@register.filter
def exclude(qs, pattens):
    if not qs or not pattens: return qs
    pattens = getPattens(pattens)
    return qs.exclude(**pattens)

@register.filter
def get(qs, pattens):
    if not qs or not pattens: return None
    result = filter(qs, pattens)
    return result.first() if result else None

@register.filter
def distinct(qs):
    if not qs: return None
    return qs.distinct()

@register.filter
def order_by(qs, odb):
    if not qs: return qs
    odb = odb.split(',')
    return qs.order_by(*odb)

@register.filter
def values(qs:'QuerySet', values):
    if not qs: return qs
    vals = values.split(',')
    return qs.values(*vals)

@register.filter
def values_list(qs, values):
    if not qs: return qs
    vals = values.split(',')
    return qs.values_list(*vals, flat=True)

@register.filter
def values_list_qs(qs, attrName):
    if not qs: return qs
    if not hasattr(qs.first(), attrName): return qs
    qsids = qs.values_list(attrName, flat=True)
    attr = getattr(qs.first(), attrName)
    oc = type(attr)
    return oc.objects.filter(pk__in=qsids)

@register.filter
def first(qs, count=1):
    if not qs: return qs
    if count == 1: return qs.first()
    cc = len(qs) if count > len(qs) else count
    return qs[:cc]

@register.filter
def last(qs, count=1):
    if not qs: return qs
    if count == 1: return qs.last()
    cc = len(qs) if count > len(qs) else count
    qs = list(reversed(qs))
    return list(reversed(qs[:cc]))


@register.filter
def merge(qsA, qsB) -> 'QuerySet':
    return qsA | qsB



@register.filter
def select_related(qs:'QuerySet', fields:'str') -> 'QuerySet':
    if not qs or not fields: return qs
    fields = fields.split(',')
    return qs.select_related(*fields)
@register.filter
def prefetch_related(qs:'QuerySet', fields:'str') -> 'QuerySet':
    if not qs or not fields: return qs
    fields = fields.split(',')
    return qs.prefetch_related(*fields)






@register.simple_tag
def filter_simple(qs, **kwargs):
    if not qs: return qs
    return qs.filter(**kwargs)




@register.simple_tag
def filter_by_time(qs:'QuerySet', fieldName:'str'='time', **kwargs) -> 'QuerySet':
    if not qs: return qs
    fQ = Q()
    fQ &= _fQ_filter_time_by_days(fieldName, **kwargs)
    fQ &= _fQ_filter_time_by_date(fieldName, **kwargs)
    fQ &= _fQ_filter_time_by_year(fieldName, **kwargs)
    fQ &= _fQ_filter_time_by_month(fieldName, **kwargs)
    fQ &= _fQ_filter_time_by_day(fieldName, **kwargs)
    return qs.filter(fQ)

@register.simple_tag
def order_by_kwargs(qs:'QuerySet', step:'str'=',', **kwargs) -> 'QuerySet':
    """ field='aaa,bbb'
    """
    if not kwargs: return qs
    cases = _order_by_kwargs_get_cases(step=step, **kwargs)
    return qs.order_by(*cases)






# filter_by_time
def _fQ_filter_time_by_days(fieldName:'str', days:'int'=None, **kwargs) -> 'Q':
    if days is None: return Q()
    field = '%s__date__gte' %(fieldName)
    value = timezone.now() - timedelta(days=days)
    return Q(**{field: value})
# def _fQ_filter_time_by_date(fieldName:'str', date:'int'=None, **kwargs) -> 'Q':
#     if date is None: return Q()
#     field = '%s__date' %(fieldName)
#     value = MyTime.formatDatetime(date).date()
#     return Q(**{field: value})
def _fQ_filter_time_by_year(fieldName:'str', year:'int'=None, **kwargs) -> 'Q':
    if year is None: return Q()
    field = '%s__year' %(fieldName)
    return Q(**{field: year})
def _fQ_filter_time_by_month(fieldName:'str', month:'int'=None, **kwargs) -> 'Q':
    if month is None: return Q()
    field = '%s__month' %(fieldName)
    return Q(**{field: month})
def _fQ_filter_time_by_day(fieldName:'str', day:'int'=None, **kwargs) -> 'Q':
    if day is None: return Q()
    field = '%s__day' %(fieldName)
    return Q(**{field: day})




# ex_order_by
def _order_by_kwargs_get_cases(step:'str'=',', **kwargs) -> 'list[Case]':
    cases = list(map(lambda k: _order_by_kwarg_2_case(k, kwargs[k], step=step), kwargs))
    keys = kwargs.keys()
    return unzipList(list(zip(cases, keys)))
def _order_by_kwarg_2_case(field:'str', values:'str', step:'str'=',') -> 'Case':
    def _val_2_when(i:'int', val:'str') -> 'When':
        return When(**{field: val}, then=V(i))
    valueList = values.split(step)
    whens = list(map(lambda a: _val_2_when(a[0], a[1]), enumerate(valueList)))
    return Case(
        *whens,
        default=V(len(whens)),
    )








