from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import generic

from . import view_methods as methods

import json

class IndexView(LoginRequiredMixin, generic.View):
    def get(self, request):
        return render(request, 'SinoArchive/index.html', {})
class IncludeView(LoginRequiredMixin, generic.View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'not authenticated'}, status=403)
        return super(IncludeView, self).dispatch(request, *args, **kwargs)
    def get(self, request, **kwargs):
        templateName = request.GET.get('template_name')
        data = request.GET.get('data')
        data = json.loads(data) if data else {}
        data.update(methods.getViewKwargsData(request, **data))
        return render(request, templateName, data)

class SAFunctionView(LoginRequiredMixin, generic.View):
    def get(self, request):
        data = methods.callForgeModelFunction(request)
        data = methods.setObject2Json(data)
        return JsonResponse({'data': data})
