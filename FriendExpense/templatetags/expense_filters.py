from django import template

register = template.Library()


@register.filter
def abs_value(value):
    """取得絕對值"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value
