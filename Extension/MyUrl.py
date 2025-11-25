from urllib.parse import quote
import re



def formatUrlSearch(search:'str') -> 'dict':
    if not search: return {}
    if not isinstance(search, str): return search
    search = search[1:] if search.startswith('?') else search
    searchs = search.split('&')
    result = {}
    for s in searchs:
        kv = s.split('=')
        if not kv or not kv [0]: continue
        k = kv[0]
        v = '='.join(kv[1:]) if len(kv) >= 2 else None
        result[k] = v
    return result

def url2Dict(url:'str') -> 'dict[str,str]':
    """ url format Regex pattern
    (?P<href>
        (?P<origin>
            ((?P<protocol>.+):\/\/)?
            (?P<host>
                (?P<hostname>[^:\/\?#]+)
                (:(?P<port>\d+))?
            )
        )?
        (?P<pathname>[^\?#]+)?
    )
    (\?(?P<searchstr>[^#]+))?
    (#(?P<hash>.+))?
    """
    pattern = r'(?P<href>(?P<origin>((?P<protocol>.+):\/\/)(?P<host>(?P<hostname>[^:\/\?#]+)(:(?P<port>\d+))?))?(?P<pathname>[^\?#]+)?)(\?(?P<searchstr>[^#]+))?(#(?P<hash>.+))?'
    match = re.search(pattern, url)
    matchJson = match.groupdict()
    matchJson['search'] = formatUrlSearch(matchJson['searchstr'])
    return matchJson


def urlPathFormat(url):
    pattern = r'(?P<domain>https?://[^\/]+)?(?P<url>[^\?\#]+)?(?P<search>\?[^\#]+)?(?P<hash>\#.+)?'
    match = re.search(pattern, url)
    return match
def urlJoin(url, *paths):
    urlMatch = urlPathFormat(url)
    pathList = (urlMatch.group('url'),) + paths
    pathList = [re.split(r'[\\\/]', p) for p in pathList if p]
    pathList = [pp for p in pathList for pp in p if pp]
    pathStr = '/%s/' %('/'.join(pathList))
    domain = urlMatch.group('domain')
    domain = domain if domain else ''
    return '%s%s' %(domain, pathStr)

def closeUrlPath(url:'str') -> 'str':
    match = urlPathFormat(url)
    matchDict = match.groupdict()
    d = matchDict['domain'] if matchDict['domain'] else ''
    u = matchDict['url'] if matchDict['url'] else ''
    s = matchDict['search'] if matchDict['search'] else ''
    h = matchDict['hash'] if matchDict['hash'] else ''
    u = u if u.endswith('/') else f'{u}/'
    return '%s%s%s%s' %(d, u, s, h)
def openUrlPath(url:'str') -> 'str':
    print('987'.ljust(100, '-'))
    print(url)
    match = urlPathFormat(url)
    matchDict = match.groupdict()
    d = matchDict['domain'] if matchDict['domain'] else ''
    u = matchDict['url'] if matchDict['url'] else ''
    s = matchDict['search'] if matchDict['search'] else ''
    h = matchDict['hash'] if matchDict['hash'] else ''
    u = u[:-1] if u.endswith('/') else u
    return '%s%s%s%s' %(d, u, s, h)


def searchDict2Str(searchDict):
    if not searchDict: return ''
    def formatSearch(k, v):
        val = quote(str(v)) if v else ''
        return '%s=%s' %(k, val)
    searchStrList = [formatSearch(k, v) for k, v in searchDict.items()]
    return '&'.join(searchStrList)

def urlFormat(*paths, search={}):
    if not paths: return ''
    url = urlJoin(paths[0], *paths[1:])
    searchStr = searchDict2Str(search)
    if searchStr: return '%s?%s' %(url, searchStr)
    return url











class Url:
    _url = ''
    _search = {}
    def __init__(self, fullUrl):
        self.init_url(fullUrl)
        self.init_search(fullUrl)
    def init_url(self, fullUrl):
        url = re.findall(r'([^?#\s]+)\??.*', fullUrl)
        self._url = url[0]
    def init_search(self, fullUrl):
        search = re.findall(r'\?([^#]+)', fullUrl)
        if not search: return
        search = search[0].split('&')
        self._search = {s[:s.index('=')]: s[s.index('=')+1:] for s in search}

    def url(self, url=None):
        if not url: return self._url
        self.init_url(url)
        return self._url
    def search(self, key=None, value=None):
        if not key: return self.search_str()
        if not value: return self._search.get(key)
        self._search[key] = value
        return self._search[key]
    def full_url(self):
        search = self.search_str()
        if not search: return self._url

        return f'{self._url}?{search}'


    def search_str(self):
        search = [f'{k}={v}' for k, v in self._search.items()]
        return '&'.join(search)
