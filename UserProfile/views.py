from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import (
    HttpRequest,
    JsonResponse,
)
from django.shortcuts import render, redirect
from django.views.generic import (
    View,
    TemplateView
)

from . import models




class NormalLoginMixin(LoginRequiredMixin):
    def dispatch(self, request:'HttpRequest', *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
class AdminLoginMixin(LoginRequiredMixin):
    def dispatch(self, request:'HttpRequest', *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile:'models.UserProfile' = request.user.profile
        if (
            not request.user.is_superuser
            and (
                profile
                and not profile.is_superuser
            )
        ):
            return JsonResponse({'message': 'not login'}, status=403)
        return super().dispatch(request, *args, **kwargs)





class MyUserMethod(View):
    def get(self, request:'HttpRequest'):
        if not request.user.is_authenticated: return JsonResponse({'message': 'not login'}, status=403)
        return JsonResponse({})
    def post(self, request:'HttpRequest'):
        if not request.user.is_authenticated: return JsonResponse({'message': 'not login'}, status=403)
        return MyUserMethod.get(self, request)


class UserView(NormalLoginMixin, TemplateView):
    def get(self, request:'HttpRequest', **kwargs):
        return render(request, self.template_name, {**kwargs})
class UserAdminView(AdminLoginMixin, TemplateView):
    def get(self, request:'HttpRequest', **kwargs):
        return render(request, self.template_name, {**kwargs})



class TestView(AdminLoginMixin, View):
    def get(self, request:'HttpRequest', **kwargs):
        return JsonResponse({})

