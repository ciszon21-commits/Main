from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import dateformat, timezone

# import pytz
import re

def djTime(inTime):
    # inTime = '2020-04-01 11:50:50'
    if not inTime: return None
    if isinstance(inTime, str):
        return str2Time(inTime)
    if isinstance(inTime, datetime) and not inTime.tzinfo:
        return timezone.make_aware(inTime)
    return inTime
def str2Time(inTime):
    times = re.findall(r'[\d]+', inTime)
    times = list(map(int, times))
    times = times if len(times) >= 3 else [times[i] if i <= len(times)-1 else 1 for i in range(3)]
    time = datetime(*times)
    time = timezone.make_aware(time)
    return time


def timeStamp(time):
    tt = time.timestamp()
    tt = tt * 1000
    return int(tt)


def normalTime(time):
    if not time: return time
    y, m, d, h, mi, s = time.year, time.month, time.day, time.hour, time.minute, time.second
    time = datetime(y, m, d, h, mi, s)
    return timezone.make_aware(time)

def monthStart(time):
    if not time: return None
    time = time if time else timezone.now()
    if isinstance(time, str): time = djTime(time)
    y, m = time.year, time.month
    sTime = datetime(y, m, 1, 0, 0, 0)
    return timezone.make_aware(sTime)
def monthEnd(time):
    if not time: return None
    sTime = monthStart(time)
    eTime = sTime + relativedelta(months=1) - relativedelta(seconds=1)
    return eTime

def weekStart(time):
    if not time: return None
    start = time - timedelta(days=time.weekday())
    y, m, d = start.year, start.month, start.day
    sTime = datetime(y, m, d, 0, 0, 0)
    return timezone.make_aware(sTime)
def weekEnd(time):
    if not time: return None
    start = weekStart(time)
    end = start + relativedelta(weeks=1) - relativedelta(seconds=1)
    return end

def dayStart(time=None):
    time = time if time else timezone.now()
    if isinstance(time, str): time = djTime(time)
    y, m, d = time.year, time.month, time.day
    sTime = datetime(y, m, d, 0, 0, 0)
    return timezone.make_aware(sTime)
    # time = timezone.make_aware(sTime)
    # return timezomeMakeAwake(time)
def dayEnd(time=None):
    time = time if time else timezone.now()
    if isinstance(time, str): time = djTime(time)
    y, m, d = time.year, time.month, time.day
    eTime = datetime(y, m, d, 23, 59, 59)
    return timezone.make_aware(eTime)

# def timezomeMakeAwake(time):
#     ptz = pytz.timezone(settings.TIME_ZONE)
#     time = timezone.localtime(time, ptz)
#     # time = timezone.make_aware(time)
#     return time


def formatDatetime(timeStr:str, beTimezone:'bool'=True) -> 'timezone':
    timeStr = str(timeStr)
    if not timeStr: return None
    if isinstance(timeStr, datetime): return timeStr
    format = r'(?P<y>\d{3,4})[\-\/\.](?P<m>\d{2})([\-\/\.](?P<d>\d{2}))?(.?(?P<h>\d{2})(:(?P<i>\d{2}))?(:(?P<s>\d{2}))?(:(?P<f>\d{3,6}))?)?'
    search = re.search(format, timeStr)
    if not search: return None
    y = search.group('y') if search.group('y') else 1911
    m = search.group('m') if search.group('m') else 1
    d = search.group('d') if search.group('d') else 1
    h = search.group('h') if search.group('h') else 0
    i = search.group('i') if search.group('i') else 0
    s = search.group('s') if search.group('s') else 0
    y, m, d = int(y), int(m), int(d)
    h, i, s = int(h), int(i), int(s)
    y = y if y>1911 else y+1911
    time = datetime(y, m, d, h, i, s)
    if not beTimezone: return time
    return timezone.make_aware(time)
def getFormatDatetimeRange(st, et):
    st = formatDatetime(st)
    et = formatDatetime(et)
    return (st, et)
def getFormatMonthRange(st, et):
    st = formatDatetime(st)
    if st:
        st = datetime(st.year, st.month, 1)
        st = timezone.make_aware(st)
    et = formatDatetime(et)
    if et:
        et = et + relativedelta(months=1)
        et = datetime(et.year, et.month, 1) - relativedelta(seconds=1)
        et = timezone.make_aware(et)
    return (st, et)


def getTodayRange(format='%Y-%m-%d %H:%M:%S'):
    ns = dateformat.format(timezone.now(), 'Y-m-d')
    return getDateRangeByStr(ns, ns, format)
def getDateRangeByStr(st=None, et=None, format='%Y-%m-%d %H:%M:%S', **kwargs):
    st = st if st else '2000-01-01'
    st = timezone.make_aware(datetime.strptime(f'{st} 00:00:00', format))
    ns = dateformat.format(timezone.now(), 'Y-m-d')
    et = et if et else ns
    et = timezone.make_aware(datetime.strptime(f'{et} 23:59:59', format))
    return (st, et)
