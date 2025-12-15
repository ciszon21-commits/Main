from django.http import (
    HttpRequest,
    JsonResponse,
)
from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, logout

from SinoErrorPage.views import ErrorView




class LoginView(View):
    def get(self, request:'HttpRequest', **kwargs):
        return ErrorView.get(self, request, status_code=403, **kwargs)

class LogoutView(View):
    def get(self, request:'HttpRequest', **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return redirect('/')

