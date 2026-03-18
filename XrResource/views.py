from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from .models import EquipmentCategory, XrEquipment, GoProAccessory, VrComputer, XrSupportRecord, GoProRentalRecord
from .forms import EquipmentCategoryForm, XrEquipmentForm, GoProAccessoryForm, VrComputerForm, XrSupportRecordForm, GoProRentalRecordForm

def vr_section(request):
    """VR 設備專區 (重構版)"""
    # 1. 電腦 Table
    computers = VrComputer.objects.all()
    
    # 2. 頭盔 Table (透過名稱篩選)
    headsets = XrEquipment.objects.filter(
        models.Q(name__icontains='頭盔') | 
        models.Q(category__name__icontains='頭盔')
    ).distinct().select_related('category')
    
    # 3. 其他 Table (VR 相關但非頭盔)
    others = XrEquipment.objects.filter(
        models.Q(name__icontains='VR') | 
        models.Q(category__name__icontains='VR')
    ).exclude(
        pk__in=headsets.values_list('pk', flat=True)
    ).distinct().select_related('category')

    context = {
        'vr_computers': computers,
        'vr_headsets': headsets,
        'vr_others': others,
    }
    return render(request, 'XrResource/vr_section.html', context)

def gopro_section(request):
    """GoPro 專區 (重構版)"""
    # 這裡假設 GoPro 相關資產都在 GoProAccessory 中
    # 1. 主機 Table
    hosts = GoProAccessory.objects.filter(name__icontains='主機')
    
    # 2. 電池 Table
    batteries = GoProAccessory.objects.filter(name__icontains='電池')
    
    # 3. 記憶卡 Table
    sd_cards = GoProAccessory.objects.filter(name__icontains='記憶卡')
    
    # 4. 其他 Table
    all_gopro = GoProAccessory.objects.all()
    others = all_gopro.exclude(
        pk__in=hosts.values_list('pk', flat=True)
    ).exclude(
        pk__in=batteries.values_list('pk', flat=True)
    ).exclude(
        pk__in=sd_cards.values_list('pk', flat=True)
    )

    context = {
        'gp_hosts': hosts,
        'gp_batteries': batteries,
        'gp_sd_cards': sd_cards,
        'gp_others': others,
    }
    return render(request, 'XrResource/gopro_section.html', context)

# 簡易 CRUD 處理 (後續可擴充為 AJAX)
def delete_item(request, model_name, pk):
    models_map = {
        'equipment': XrEquipment,
        'accessory': GoProAccessory,
        'computer': VrComputer,
        'support': XrSupportRecord,
        'rental': GoProRentalRecord,
        'category': EquipmentCategory,
    }
    model = models_map.get(model_name)
    if model:
        item = get_object_or_404(model, pk=pk)
        item.delete()
        messages.success(request, '刪除成功')
    return redirect(request.META.get('HTTP_REFERER', 'XrResource:dashboard'))
