import re

from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.simple_tag
def user_sindex(user:'User') -> 'str':
    if not user: return ''
    if not user.username: return ''
    pattern = r'(\w+)?[\\\/\|]?(?P<sindex>\d+)'
    match = re.search(pattern, user.username)
    if not match: return ''
    return match.group('sindex')