import re

from . import basic


PROJ_NO_PATTERN = r'(?P<pNo>[\w\d]+)(-(?P<tNo>[\w\d]+))?'
PROJECT_TENDER_NAMES = basic.PROJECT_TENDER_NAMES




def formatProjNos(projNos:'list[str]|str', excludeNone:'bool'=True) -> 'list[dict[str,str]]':
    if not projNos: return []
    projNos = projNos if isinstance(projNos, list) else [projNos]
    fptNos = [formatProjNo(p) for p in projNos]
    if excludeNone:
        fptNos = [i for i in fptNos if i]
    return fptNos
def formatProjNo(projNo:'str') -> 'dict[str,str]':
    if not projNo: return {}
    match = re.search(PROJ_NO_PATTERN, projNo)
    if not match: return {}
    matchDict =  match.groupdict()
    fullNo = _formatFullNo(matchDict)
    tenderNo = _formatTenderNo(matchDict)
    tenderName = _formatTenderName(matchDict)
    return {
        'fullNo': fullNo.upper(),
        'projNo': matchDict.get('pNo').upper(),
        'tenderNo': tenderNo.upper(),
        'tenderName': tenderName,
        '_fullNo': fullNo,
        '_projNo': matchDict.get('pNo'),
        '_tenderNo': tenderNo,
    }
def _formatFullNo(matchDict:'dict') -> 'str':
    pNo = matchDict.get('pNo', '')
    tNo = matchDict.get('tNo', '')
    if not tNo: return '%s' %(pNo)
    if tNo.upper() == 'TenderA'.upper(): return '%s' %(pNo)
    return '%s-%s' %(pNo, tNo)
def _formatTenderNo(matchDict:'dict') -> 'str':
    tNo = matchDict.get('tNo', '')
    if tNo: return tNo
    return 'TenderA'
def _formatTenderName(matchDict:'dict') -> 'str':
    pNo = matchDict.get('pNo', '')
    tNo = matchDict.get('tNo', '')
    if not all([pNo, tNo]): return ''
    tNameDict = PROJECT_TENDER_NAMES.get(pNo.upper(), {})
    tName = tNameDict.get(tNo.upper(), '')
    return tName



def splitProjNos(projNos:'list[str]') -> 'list[tuple[str,str]]':
    ptNos = [splitProjNo(p) for p in projNos]
    ptNos = [pt for pt in ptNos if any(pt)]
    return ptNos
def splitProjNo(projNo:'str') -> 'tuple[str,str]':
    if not projNo: return (None, None)
    match = re.search(PROJ_NO_PATTERN, projNo)
    if not match: return (None, None)
    matchDict = match.groupdict()
    return (
        matchDict.get('pNo').upper(),
        matchDict.get('tNo'),
    )
