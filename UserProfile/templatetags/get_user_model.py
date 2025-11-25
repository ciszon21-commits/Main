from datetime import timedelta
from django.db.models import Q
from django.db.models import QuerySet
from django import template
from django.contrib.auth.models import User
from django.utils import timezone

from Extension import MyMath
from UserProfile import models as UserModels

import re

register = template.Library()



@register.simple_tag
def get_all_users():
    fQ = Q(is_active=True)
    return User.objects.filter(fQ)

@register.simple_tag
def get_all_userprofiles():
    return UserModels.UserProfile.objects.all()

@register.simple_tag
def get_all_groups():
    return UserModels.Group.objects.all()




@register.simple_tag
def get_joined_groups(user:'User') -> 'QuerySet[User]':
    return UserModels.Group.objects.get_joined_groups(user)





@register.simple_tag
def get_user_response_logs(dt='', date='', year=0, month=0, day=0):
    if dt == 'yesterday':
        date = timezone.now() - timedelta(days=1)
        lf = Q(time__year=date.year) & Q(time__month=date.month) & Q(time__day=date.day)
        return UserModels.ResponseLog.objects.filter(lf)
    elif dt == 'today':
        date = timezone.now()
        lf = Q(time__year=date.year) & Q(time__month=date.month) & Q(time__day=date.day)
        return UserModels.ResponseLog.objects.filter(lf)
    elif date:
        pattern = r'(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)'
        dm = re.search(pattern, date)
        if not dm: return UserModels.ResponseLog.objects.filter(pk=-1)
        year, month, day = ymdFormat(dm.group('year'), dm.group('month'), dm.group('day'))
        lf = Q(time__year=year) & Q(time__month=month) & Q(time__day=day)
        return UserModels.ResponseLog.objects.filter(lf)
    elif year and month and day:
        year, month, day = ymdFormat(year, month, day)
        lf = Q(time__year=year) & Q(time__month=month) & Q(time__day=day)
        return UserModels.ResponseLog.objects.filter(lf)
    return UserModels.ResponseLog.objects.all()

def ymdFormat(year, month, day):
    year = MyMath.convertToNum(year, int)
    month = MyMath.convertToNum(month, int)
    day = MyMath.convertToNum(day, int)
    year = MyMath.inMaxMin(int(year), 3000, 2000)
    month = MyMath.inMaxMin(int(month), 12, 1)
    day = MyMath.inMaxMin(int(day), 31, 1)
    return year, month, day

