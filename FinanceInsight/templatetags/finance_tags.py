from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """從字典中取得指定key的值"""
    if dictionary is None or not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
