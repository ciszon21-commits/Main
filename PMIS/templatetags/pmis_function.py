from django import template

from PMIS import pmis_function as PmisFunc

register = template.Library()



@register.simple_tag
def format_proj_no(ptNo:'str'='', projNo:'str'='', tenderNo:'str'='') -> 'dict':
    if ptNo: return PmisFunc.formatProjNo(ptNo)
    return PmisFunc.formatProjNo('%s-%s' %(projNo, tenderNo))


