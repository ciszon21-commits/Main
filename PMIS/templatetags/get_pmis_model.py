from django.db.models import QuerySet
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from django import template

from SinoExtension.tools.time import format_datetime
from PMIS import models as PMISModels
from UserProfile import models as UserModels
register = template.Library()



@register.simple_tag
def get_sso_token(token:'str') -> 'PMISModels.SSO_Token':
    if not token: return None
    return PMISModels.SSO_Token.objects.filter(Token=token).first()


@register.simple_tag
def get_line_group_mapping(gmId:'str') -> 'PMISModels.LineGroupMapping':
    if not gmId: return None
    return PMISModels.LineGroupMapping.objects.filter(Id=gmId).first()

@register.simple_tag
def get_line_group_mappings(projno=''):
    if projno == 'comment': return PMISModels.LineGroupMapping.objects.space_comment()
    if projno == 'all': return PMISModels.LineGroupMapping.objects.all()
    if projno: return PMISModels.LineGroupMapping.objects.filter(Project__iexact=projno)
    return PMISModels.LineGroupMapping.objects.none()

@register.simple_tag
def get_line_messages(
        group: 'PMISModels.LineGroupMapping' = None,
        days: 'int' = None,
        starttime: 'datetime' = None,
        endtime: 'datetime' = None
    ) -> 'QuerySet[PMISModels.LineMessage]':
    if not any([group, days, starttime, endtime]):
        return PMISModels.LineMessage.objects.none()
    messages = PMISModels.LineMessage.objects.all()
    messages = filterLineMessagesByGroup(messages, group)
    messages = filterLineMessages(messages, days, starttime, endtime)
    return messages
def filterLineMessagesByGroup(
        messages: 'QuerySet[PMISModels.LineMessage]',
        group: 'PMISModels.LineGroupMapping' = None,
    ) -> 'QuerySet[PMISModels.LineMessage]':
    if not group: return messages
    if group.Id == 'comment':
        return messages.filter(GroupId__iexact=group.Id)
    return messages.filter(GroupId=group.Id)
def filterLineMessages(
        qs:'QuerySet[PMISModels.LineMessage]',
        days:int=None,
        starttime:datetime=None,
        endtime:datetime=None
    ) -> 'QuerySet[PMISModels.LineMessage]':
    endtime = endtime if endtime else starttime + timedelta(days=days)
    # FIXME 想辦法用 timezone 來找出 8 這個結果
    # print(f'{starttime}({starttime.tzinfo})', '\t-\t', f'{endtime}({endtime.tzinfo})')
    starttime = format_datetime(starttime) + timedelta(hours=8)
    endtime = format_datetime(endtime) + timedelta(hours=8) + timedelta(seconds=1)
    # print(f'{starttime}({starttime.tzinfo})', '\t-\t', f'{endtime}({endtime.tzinfo})')
    qs = qs.filter(CreateDate__range=[starttime, endtime])
    return qs


@register.simple_tag
def get_center_departments():
    return PMISModels.CenterDept.objects.all()


@register.simple_tag
def get_user_department(user:'UserModels.UserProfile') -> 'PMISModels.CenterDept':
    if not user: return None
    depaName = user.get_department_name()
    if not depaName: return None
    fQ = Q(DeptName=depaName) | Q(DeptShortName=depaName)
    return PMISModels.CenterDept.objects.filter(fQ).first()
