from django.conf import settings
from django.db import connection
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin



DEBUG = settings.DEBUG


class QCRequest(HttpRequest):
    query_count: 'int'

class QueryCountMiddleware(MiddlewareMixin):
    def process_request(self, request:'QCRequest'):
        setRequestQueryCount(request)
    def process_response(self, request:'QCRequest', response):
        printRequestQueryCount(request)
        return response



def setRequestQueryCount(request:'QCRequest'):
    if not DEBUG: return
    request.query_count = len(connection.queries)
def printRequestQueryCount(request:'QCRequest'):
    if not DEBUG: return
    if not hasattr(request, 'query_count'): return
    lcq = len(connection.queries)
    rqc = request.query_count
    tqc = lcq - rqc
    msg = ''
    msg += '\nDB query count: %s' %(tqc)
    print(msg)

