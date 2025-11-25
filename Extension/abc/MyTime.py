import re

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import dateformat, timezone



def dj_time(inTime):
    # inTime = '2020-04-01 11:50:50'
    if isinstance(inTime, str):
        return str_2_time(inTime)
    if isinstance(inTime, datetime) and not inTime.tzinfo:
        return timezone.make_aware(inTime)
    return inTime
def str_2_time(inTime):
    times = re.findall(r'[\d]+', inTime)
    times = list(map(int, times))
    times = times if len(times) >= 3 else [times[i] if i <= len(times)-1 else 1 for i in range(3)]
    time = datetime(*times)
    time = timezone.make_aware(time)
    return time


def time_stamp(time):
    tt = time.timestamp()
    tt = tt * 1000
    return int(tt)


def normal_time(time):
    if not time: return time
    y, m, d, h, mi, s = time.year, time.month, time.day, time.hour, time.minute, time.second
    time = datetime(y, m, d, h, mi, s)
    return timezone.make_aware(time)

def month_start(time):
    if not time: return None
    time = time if time else timezone.now()
    if isinstance(time, str): time = dj_time(time)
    y, m = time.year, time.month
    sTime = datetime(y, m, 1, 0, 0, 0)
    return timezone.make_aware(sTime)
def month_end(time):
    if not time: return None
    sTime = month_start(time)
    eTime = sTime + relativedelta(months=1) - relativedelta(seconds=1)
    return eTime

def week_start(time):
    if not time: return None
    start = time - timedelta(days=time.weekday())
    y, m, d = start.year, start.month, start.day
    sTime = datetime(y, m, d, 0, 0, 0)
    return timezone.make_aware(sTime)
def week_end(time):
    if not time: return None
    start = week_start(time)
    end = start + relativedelta(weeks=1) - relativedelta(seconds=1)
    return end

def day_start(time=None):
    time = time if time else timezone.now()
    if isinstance(time, str): time = dj_time(time)
    y, m, d = time.year, time.month, time.day
    sTime = datetime(y, m, d, 0, 0, 0)
    return timezone.make_aware(sTime)
    # time = timezone.make_aware(sTime)
    # return timezomeMakeAwake(time)
def day_end(time=None):
    time = time if time else timezone.now()
    if isinstance(time, str): time = dj_time(time)
    y, m, d = time.year, time.month, time.day
    eTime = datetime(y, m, d, 23, 59, 59)
    return timezone.make_aware(eTime)



def format_datetime_json(timeStr:'str') -> 'dict':
    timeStr = str(timeStr)
    if not timeStr: return None
    if isinstance(timeStr, datetime): return timeStr
    format = r'(?P<y>\d{4})-(?P<m>\d{2})(-(?P<d>\d{2}))?(.?(?P<h>\d{2})(:(?P<i>\d{2}))?(:(?P<s>\d{2}))?)?'
    match = re.search(format, timeStr)
    if not match: return None
    return match.groupdict()
def format_datetime(timeStr:str) -> 'timezone':
    if isinstance(timeStr, datetime): return timeStr
    if not timeStr: return None
    timeJson = format_datetime_json(timeStr)
    if not timeJson: return None
    y = timeJson['y'] if timeJson.get('y') else 1911
    m = timeJson['m'] if timeJson.get('m') else 1
    d = timeJson['d'] if timeJson.get('d') else 1
    h = timeJson['h'] if timeJson.get('h') else 0
    i = timeJson['i'] if timeJson.get('i') else 0
    s = timeJson['s'] if timeJson.get('s') else 0
    y, m, d = int(y), int(m), int(d)
    h, i, s = int(h), int(i), int(s)
    time = datetime(y, m, d, h, i, s)
    return timezone.make_aware(time)
def get_format_datetime_range(st, et):
    st = format_datetime(st)
    et = format_datetime(et)
    return (st, et)
def get_format_month_range(st, et):
    st = format_datetime(st)
    if st:
        st = datetime(st.year, st.month, 1)
        st = timezone.make_aware(st)
    et = format_datetime(et)
    if et:
        et = et + relativedelta(months=1)
        et = datetime(et.year, et.month, 1) - relativedelta(seconds=1)
        et = timezone.make_aware(et)
    return (st, et)


def get_today_range(format='%Y-%m-%d %H:%M:%S'):
    ns = dateformat.format(timezone.now(), 'Y-m-d')
    return get_date_range_by_str(ns, ns, format)
def get_date_range_by_str(st=None, et=None, format='%Y-%m-%d %H:%M:%S', **kwargs):
    st = st if st else '2000-01-01'
    st = timezone.make_aware(datetime.strptime(f'{st} 00:00:00', format))
    ns = dateformat.format(timezone.now(), 'Y-m-d')
    et = et if et else ns
    et = timezone.make_aware(datetime.strptime(f'{et} 23:59:59', format))
    return (st, et)


def get_timezone_hours(time:'datetime') -> 'int':
    timeStr = str(time)
    pattern = r'(?P<pm>[\+\-])(?P<tzh>\d{2}):(?P<tzm>\d{2})'
    match = re.search(pattern, timeStr)
    if not match: return 0
    tzJson = match.groupdict()
    pm = tzJson.get('pm', '+')
    tzh = tzJson.get('tzh', 0)
    pm = 1 if pm == '+' else -1
    tzh = int(tzh)
    return pm * tzh
def get_timezone(time:'datetime') -> 'timedelta':
    tzHours = get_timezone_hours(time)
    return timedelta(hours=tzHours)
