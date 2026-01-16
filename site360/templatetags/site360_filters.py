from django import template

register = template.Library()

@register.filter
def after_underscore(value):
    """
    Returns the substring after the first underscore.
    If no underscore is found, returns the original string.
    """
    if not isinstance(value, str):
        return value
    if "_" in value:
        return value.split("_", 1)[1]
    return value
