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

@register.filter
def get_item(dictionary, key):
    """
    Access dictionary item by key in templates.
    Usage: {{ mydict|get_item:mykey }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
