import re

def inMaxMin(num, max=0, min=0):
    if num > max: return max
    if num < min: return min
    return num

def convertToNum(text: str, method):
    if not text: return 0
    tn = re.sub(r'[^\d\.\-]+', '', text)
    return method(tn)
