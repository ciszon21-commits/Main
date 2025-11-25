import re
from typing import TypedDict

from django.core.handlers.wsgi import WSGIRequest


def request_data_2_dict(request:'WSGIRequest', noneList:'list'=['']) -> dict:
    result = {}
    result.update(request_get_data_2_dict(request, noneList))
    result.update(request_post_data_2_dict(request, noneList))
    result.update(request_put_data_2_dict(request, noneList))
    return result
def request_get_data_2_dict(request, noneList:'list'=[]) -> dict:
    reqData = request.GET.dict()
    return {k: request_value_format(v, noneList) for k, v in reqData.items()}
def request_post_data_2_dict(request, noneList:'list'=[]) -> dict:
    reqData = request.POST.dict()
    return {k: request_value_format(v, noneList) for k, v in reqData.items()}
def request_put_data_2_dict(request, noneList:'list'=[]):
    if not hasattr(request, 'data'): return {}
    dataDict = request.data if isinstance(request.data, dict) else request.data.dict()
    return {k: request_value_format(v, noneList) for k, v in dataDict.items()}



def request_value_format(val, noneList:'list[str]'=[]):
    val = val[0] if isinstance(val, list) else val
    if not isinstance(val, str): return val
    lowVal = val.lower()
    if request_value_is_none(lowVal, noneList): return None
    boolVal = request_boolean_value_format(lowVal)
    if boolVal is not None: return boolVal
    intVal = request_int_value_format(lowVal)
    if intVal is not None: return intVal
    floVal = request_float_value_format(lowVal)
    if floVal is not None: return floVal
    return val

def request_value_is_none(val:'str', noneList:'list[str]') -> 'bool':
    nones = ['none']
    if val in nones: return True
    if val in noneList: return True
    return False
def request_boolean_value_format(val:'str') -> 'bool':
    trues = ['true', 'on']
    falses = ['false', 'off']
    if val in trues: return True
    elif val in falses: return False
    return None
def request_int_value_format(val:'str') -> 'int':
    if not val.isdigit(): return None
    if '.' not in val: return None
    return float(val)
def request_float_value_format(val:'str') -> 'float':
    if not val.isdigit(): return None
    return int(val)




def request_2_search(request:'WSGIRequest') -> 'str':
    req = request_data_2_dict(request)
    seas = [f'{k}={v}' for k, v in req.items()]
    return '&'.join(seas)






def get_ip_path(request:'WSGIRequest') -> 'str':
    meta = request.META
    ipPath = meta.get('HTTP_X_FORWARDED_FOR')
    ipPath = ipPath.split(',')[0] if ipPath else meta.get('REMOTE_ADDR', '')
    return ipPath
def get_server_ip_path(request:'WSGIRequest') -> 'str':
    return request.META.get('SERVER_ADDR', '-1.-1.-1.-1')



class MetaAgentDetail(TypedDict):
    phone: 'bool'
    pc: 'bool'
    isMobile: 'bool'
def meta_detail(request:'WSGIRequest') -> 'MetaAgentDetail':
    agent = request.META.get('HTTP_USER_AGENT', '')
    pc = re.search(r'(window|mac)', agent, re.IGNORECASE)
    ph = re.search(r'(android|ios)', agent, re.IGNORECASE)
    mo = re.search(r'(mobile)', agent, re.IGNORECASE)
    return {
        'phone': ph.group(0) if ph else ph,
        'pc': pc.group(0) if pc else pc,
        'isMobile': True if mo else False,
    }
