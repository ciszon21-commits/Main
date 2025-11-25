import re


IGNORE_KEYS = [
    '_'
]



def requestData2Dict(request, noneList:'list[str]'=[], **kwargs):
    result = {}
    result.update(requestGETData2Dict(request, noneList))
    result.update(requestPOSTData2Dict(request, noneList))
    result.update(requestPUTData2Dict(request, noneList))
    result = ignoreRequestsKeys(request, result, **kwargs)
    return result
def requestGETData2Dict(request, noneList:'list[str]'=[]):
    return {k: requestValueFormat(v, noneList) for k, v in request.GET.items()}
def requestPOSTData2Dict(request, noneList:'list[str]'=[]):
    return {k: requestValueFormat(v, noneList) for k, v in request.POST.items()}
def requestPUTData2Dict(request, noneList:'list[str]'=[]):
    if not hasattr(request, 'data'): return {}
    dataDict = request.data if isinstance(request.data, dict) else request.data.dict()
    return {k: requestValueFormat(v, noneList) for k, v in dataDict.items()}
def ignoreRequestsKeys(request, data:'dict', ignoreKeys:'bool'=True, **kwargs):
    if not ignoreKeys: return data
    data = {k: v for k, v in data.items() if not k in IGNORE_KEYS}
    return data



def requestValueFormat(val, noneList:'list[str]'=[]):
    val = val[0] if isinstance(val, list) else val
    if not isinstance(val, str): return val
    lowVal = val.lower()
    if requestValueIsNone(lowVal, noneList): return None
    boolVal = requestBooleanValueFormat(lowVal)
    if boolVal is not None: return boolVal
    intVal = requestIntValueFormat(lowVal)
    if intVal is not None: return intVal
    floVal = requestFloatValueFormat(lowVal)
    if floVal is not None: return floVal
    return val


def requestValueIsNone(val:'str', noneList:'list[str]') -> 'bool':
    nones = ['none']
    if val in nones: return True
    if val in noneList: return True
    return False
def requestBooleanValueFormat(val:'str') -> 'bool':
    trues = ['true', 'on']
    falses = ['false', 'off']
    if val in trues: return True
    elif val in falses: return False
    return None
def requestIntValueFormat(val:'str') -> 'int':
    if not val.isdigit(): return None
    if not '.' in val: return None
    return float(val)
def requestFloatValueFormat(val:'str') -> 'float':
    if not val.isdigit(): return None
    return int(val)





def request2Search(request):
    req = requestData2Dict(request)
    seas = [f'{k}={v}' for k, v in req.items()]
    return '&'.join(seas)






def getIpPath(request):
    meta = request.META
    ipPath = meta.get('HTTP_X_FORWARDED_FOR')
    ipPath = ipPath.split(',')[0] if ipPath else meta.get('REMOTE_ADDR', '')
    return ipPath
def getServerIpPath(request):
    return request.META.get('SERVER_ADDR', '-1.-1.-1.-1')


def metaDetail(request):
    agent = request.META.get('HTTP_USER_AGENT', '')
    pc = re.search(r'(window|mac)', agent, re.IGNORECASE)
    ph = re.search(r'(android|ios)', agent, re.IGNORECASE)
    mo = re.search(r'(mobile)', agent, re.IGNORECASE)
    return {
        'phone': ph.group(0) if ph else ph,
        'pc': pc.group(0) if pc else pc,
        'isMobile': True if mo else False,
    }
