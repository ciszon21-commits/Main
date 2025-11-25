from django import template
from django.contrib.auth.models import User

from UserProfile import models as UserModels

register = template.Library()



@register.filter
def is_superuser(user:'User') -> 'bool':
    if user.is_superuser: return True
    profile = UserModels.UserProfile.objects.filter(user=user).first()
    if not profile: return False
    if profile.is_superuser: return True
    return False

