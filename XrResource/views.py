from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from .models import EquipmentCategory, XrEquipment, XrSupportRecord, GoProRentalRecord
from .forms import EquipmentCategoryForm, XrEquipmentForm, XrSupportRecordForm, GoProRentalRecordForm

def vr_section(request):
    """VR 設備專區 (統一模型版)"""
    selected_statuses = request.GET.getlist('status')
    vr_items = XrEquipment.objects.filter(section='vr').select_related('category')
    
    if selected_statuses:
        vr_items = vr_items.filter(status__in=selected_statuses)
    
    # 分類指取
    context = {
        'vr_computers': vr_items.filter(models.Q(name__icontains='電腦') | models.Q(category__name__icontains='電腦')),
        'vr_headsets': vr_items.filter(models.Q(name__icontains='頭盔') | models.Q(category__name__icontains='頭盔')),
        'vr_others': vr_items.exclude(
            models.Q(name__icontains='電腦') | models.Q(category__name__icontains='電腦') |
            models.Q(name__icontains='頭盔') | models.Q(category__name__icontains='頭盔')
        ),
        'categories': EquipmentCategory.objects.all(),
        'eq_form': XrEquipmentForm(),
        'status_choices': XrEquipment.STATUS_CHOICES,
        'selected_statuses': selected_statuses,
    }
    return render(request, 'XrResource/vr_section.html', context)

def gopro_section(request):
    """GoPro 專區 (統一模型版)"""
    selected_statuses = request.GET.getlist('status')
    gp_items = XrEquipment.objects.filter(section='gopro').select_related('category')
    
    if selected_statuses:
        gp_items = gp_items.filter(status__in=selected_statuses)
    
    context = {
        'gp_hosts': gp_items.filter(models.Q(name__icontains='主機') | models.Q(category__name__icontains='主機')),
        'gp_batteries': gp_items.filter(models.Q(name__icontains='電池') | models.Q(category__name__icontains='電池')),
        'gp_sd_cards': gp_items.filter(models.Q(name__icontains='記憶卡') | models.Q(category__name__icontains='記憶卡')),
        'gp_others': gp_items.exclude(
            models.Q(name__icontains='主機') | models.Q(category__name__icontains='主機') |
            models.Q(name__icontains='電池') | models.Q(category__name__icontains='電池') |
            models.Q(name__icontains='記憶卡') | models.Q(category__name__icontains='記憶卡')
        ),
        'categories': EquipmentCategory.objects.all(),
        'eq_form': XrEquipmentForm(),
        'status_choices': XrEquipment.STATUS_CHOICES,
        'selected_statuses': selected_statuses,
    }
    return render(request, 'XrResource/gopro_section.html', context)

def equipment_save(request, pk=None):
    """新增或編輯設備"""
    if pk:
        equipment = get_object_or_404(XrEquipment, pk=pk)
    else:
        equipment = None

    if request.method == 'POST':
        form = XrEquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, '資料已儲存')
        else:
            messages.error(request, '儲存失敗，請檢查欄位格式')
    
    return redirect(request.META.get('HTTP_REFERER', 'XrResource:vr_section'))

def delete_item(request, model_name, pk):
    """刪除物件"""
    models_map = {
        'equipment': XrEquipment,
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
