from django import template



register = template.Library()


@register.filter
def abc_len(items):
    return len(items)

@register.filter
def abc_type(item):
    return type(item).__name__

@register.filter
def abc_str(item):
    if not item: return ''
    return str(item)

@register.filter
def abc_int(item):
    if not item: return 0
    return int(item)

@register.filter
def abc_upper(item):
    return str(item).upper()

@register.filter
def abc_lower(item):
    return str(item).lower()

@register.filter
def abc_dir(item):
    return dir(item)

@register.filter
def abc_list(item):
    return list(item)
@register.filter
def abc_list_zip(a, b):
    return list(zip(a, b))

@register.filter
def abc_dict(item):
    return dict(item)


@register.filter
def abc_set(items):
    return set(items)



@register.filter
def split(text, target=','):
    if not text: return []
    return text.split(target)


@register.filter
def abc_all(array):
    return all(array)
@register.filter
def abc_all_is(array, item):
    array = [a == item for a in array]
    return all(array)

@register.filter
def abc_any(array):
    return any(array)
@register.filter
def abc_any_is(array, item):
    array = [a == item for a in array]
    return any(array)




@register.simple_tag
def abc_range(start:'int', end:'int'=None) -> 'range':
    if not any([start, end]): return range(0)
    if end is None: return range(start)
    return range(start, end)


