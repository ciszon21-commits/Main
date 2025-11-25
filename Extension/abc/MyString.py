import base64
import json
import random
import re
import string
from uuid import UUID




INDEX_LOWER_A2Z_LIST_RANGE = list(map(chr, range(ord('a'), ord('z')+1)))
INDEX_UPPER_A2Z_LIST_RANGE = list(map(chr, range(ord('A'), ord('Z')+1)))
INDEX_CJ_LIST_RANGE = [
    '甲', '乙', '丙', '丁', '戊',
    '己', '庚', '辛', '壬', '癸',
]
INDEX_CZ_LIST_RANGE = [
    '子', '丑', '寅', '卯', '辰', '巳',
    '午', '未', '申', '酉', '戌', '亥',
]
INDEX_RANGE_LISTS = [
    INDEX_LOWER_A2Z_LIST_RANGE,
    INDEX_UPPER_A2Z_LIST_RANGE,
    INDEX_CJ_LIST_RANGE,
    INDEX_CZ_LIST_RANGE,
]




def increment_number_place(inputStr:'str') -> 'str':
    """ 數字進位 - 實作
    """
    if not inputStr or not inputStr.isdigit(): return ''
    num = int(inputStr)
    return str(num+1)
def increment_a2z_place(inputStr:'str') -> 'str':
    """ 讓 a to z 按照類似數字進位的方式進位 - 實作
    """
    if not inputStr: return ''
    s, e = inputStr[:-1], inputStr[-1]
    n = 'aa' if e in ['Z', 'z'] else chr(ord(e) + 1)
    r = '%s%s' %(s, n)
    if 'A' <= e <= 'Z':
        return r.upper()
    return r
def increment_string_place(inputStr:'str', charList:'list') -> 'str':
    """ 讓文字按照類似數字進位的方式進位 - 實作
    偉哉 GPT 生成的程式竟然可以用
    """
    chars = list(inputStr)
    carry = True
    for i in range(len(chars)-1, -1, -1):
        if not carry: continue
        index = charList.index(chars[i])
        if index == len(charList) - 1:
            chars[i] = charList[0]
        else:
            chars[i] = charList[index + 1]
            carry = False
    if carry:
        chars.insert(0, charList[0])
    return ''.join(chars)

def calculate_actual_place(inputStr:'str', charList:'list') -> 'int':
    """ 計算文字真實的位階
    """
    char2PlaceLam = lambda s: charList.index(s)+1
    prPowLam = lambda pr: pr[0] * len(charList) ** pr[1]
    chars = list(inputStr)
    places = list(map(char2PlaceLam, chars))
    pPowRan = range(len(places)-1, -1, -1)
    prs = list(zip(places, pPowRan))
    pPows = list(map(prPowLam, prs))
    return sum(pPows)




def first_place(inputStr:'str') -> 'str':
    """ 抓這個類型的文字的第一個
    """
    if not inputStr: return ''
    e = inputStr[-1]
    if e.isdigit():
        return '1'
    for tl in INDEX_RANGE_LISTS:
        if e not in tl: continue
        return tl[0]
    return ''
def increment_place(inputStr:'str') -> 'str':
    """ 讓文字按照類似數字進位的方式進位
    """
    if not inputStr: return ''
    e = inputStr[-1]
    if e.isdigit():
        return increment_number_place(inputStr)
    for tl in INDEX_RANGE_LISTS:
        if e not in tl: continue
        return increment_string_place(inputStr, tl)
    return ''

def actual_place(inputStr:'str') -> 'int':
    """ 計算文字真實的位階
    """
    if not inputStr: return -1
    e = inputStr[-1]
    if e.isdigit():
        return int(inputStr)
    for tl in INDEX_RANGE_LISTS:
        if e not in tl: continue
        return calculate_actual_place(inputStr, tl)
    return -1










def range_text(textLength:'int'=10, format:'str'='\\w\\W\\d') -> 'str':
    format = format.replace('\\w', string.ascii_lowercase)
    format = format.replace('\\W', string.ascii_uppercase)
    format = format.replace('\\d', string.octdigits)
    return ''.join(random.choice(format) for i in range(textLength))

def is_json(text:'str') -> 'bool':
    if not text: return False
    text = text if isinstance(text, str) else str(text)
    try:
        ans = json.loads(text)
        if isinstance(ans, dict): return True
        if isinstance(ans, list): return True
    except ValueError as e:
        return False
    return False


def is_email(email:'str') -> 'bool':
    if not email: return False
    pattern = r'^[^\@]+@[^\@\.]+\.[^\@]+$'
    match = re.search(pattern, email)
    return True if match else False

def is_uuid(uuid:'str|UUID') -> 'bool':
    if isinstance(uuid, UUID): return True
    if not uuid: return False
    pattern = r'[a-zA-Z0-9]{8}-?[a-zA-Z0-9]{4}-?[a-zA-Z0-9]{4}-?[a-zA-Z0-9]{4}-?[a-zA-Z0-9]{12}'
    match = re.search(pattern, str(uuid))
    return True if match else False


def safe_b64_code(b:'str') -> 'str':
    pnLen = len(b) % 4
    if pnLen == 0: return b
    return b + '='*(4-pnLen)


def str_to_b64(s):
    if not s: return ''
    se = s.encode('utf-8')
    b = base64.b64encode(se)
    return b.decode('utf-8')
def b64_to_str(b):
    if not b: return ''
    b = safe_b64_code(b)
    sb = base64.b64decode(b)
    return sb.decode('utf-8')


def str_to_list(s:'str') -> 'list[str]':
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1]
    return list(map(str_to_val, s.split(',')))




def str_to_val(s:'str'):
    s = s[1:-1] if (
        (s.startswith('\'') and s.endswith('\''))
        or (s.startswith('\"') and s.endswith('\"'))
    ) else s
    ls = s.lower()
    if _val_is_none(ls): return None
    bVal = _val_to_bool(ls)
    if bVal is not None: return bVal
    fVal = _val_to_float(ls)
    if fVal is not None: return fVal
    iVal = _val_to_int(ls)
    if iVal is not None: return iVal
    return s



def _val_is_none(val:'str') -> 'bool':
    if val in ['', 'none', 'null', 'undefined']: return True
    return False
def _val_to_bool(val:'str') -> 'bool':
    if val in ['true', 'on']: return True
    elif val in ['false', 'off']: return False
    return None
def _val_to_float(val:'str') -> 'float':
    if not val.isdigit(): return None
    if '.' not in val: return None
    return float(val)
def _val_to_int(val:'str') -> 'int':
    if not val.isdigit(): return None
    return int(val)







def range_loop(count:'int', target:'str', sList:'list[str]'=[], eList:'list[str]'=[]) -> 'list[str]':
    result = []
    for i in range(count+1):
        tls = [target for j in range(i)]
        tls = sList + tls + eList
        tlStr = '__'.join(tls)
        result.append(tlStr)
    return result




