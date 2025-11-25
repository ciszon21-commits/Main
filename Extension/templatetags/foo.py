from django import template


register = template.Library()

@register.simple_tag
def foo(arg):
    return arg


@register.simple_tag
def cls_type(i):
    return type(i).__name__
