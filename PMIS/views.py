from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render
from django.views import generic

# from . import models
from LtdCopy import models as LtdModels
from LtdCopy import serializers as LtdSerializers
from . import pmis_function as PmisFunction


class Index(generic.View):
    def get(self, request):
        context = {}
        return render(request, 'PMIS/index.html', context)

class VProject(generic.View):
    def get(self, request):
        projNo = request.GET.get('projNo')
        if not projNo: return JsonResponse({}, status=400)
        fptNo = PmisFunction.formatProjNo(projNo)
        pNo = fptNo.get('projNo')
        vproject = LtdModels.VProject.objects.search_no(proj_no=pNo)
        if not vproject: return JsonResponse({}, status=404)
        vProjSer = LtdSerializers.VProjectSerializer(vproject)
        fptNo.update(vProjSer.data)
        return JsonResponse(fptNo)
