


def formatDict(
        dd:'dict',
        noneInts:'list[int]|int'=None,
        noneStrs:'list[str]|str'=None,
        ignoreNone:'bool'=True,
    ) -> 'dict':
    dd = _formatDict_int2None(dd, noneInts)
    dd = _formatDict_str2None(dd, noneStrs)
    dd = _formatDict_ignoreNone(dd, ignoreNone)
    return dd

def _formatDict_int2None(dd:'dict', noneInts:'list[int]|int'=None) -> 'dict':
    if noneInts is None: return dd
    noneInts = noneInts if isinstance(noneInts, list) else [noneInts]
    return {k: None if v in noneInts else v for k, v in dd.items()}
def _formatDict_str2None(dd:'dict', noneStrs:'list[str]|str'=None) -> 'dict':
    if noneStrs is None: return dd
    noneStrs = noneStrs if isinstance(noneStrs, list) else [noneStrs]
    return {k: None if v in noneStrs else v for k, v in dd.items()}
def _formatDict_ignoreNone(dd:'dict', ignoreNone:'bool') -> 'dict':
    if not ignoreNone: return dd
    return {k: v for k, v in dd.items() if not v is None}
