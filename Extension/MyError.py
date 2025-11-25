from django.http import HttpResponseBadRequest


class BadRequest(HttpResponseBadRequest, BaseException):
    pass