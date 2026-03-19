from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models, transaction
from .models import EquipmentCategory, XrEquipment, XrSupportRecord, GoProRentalRecord, XrBulkItem, XrRentalRecord, XrRentalBulkItem
from .forms import EquipmentCategoryForm, XrEquipmentForm, XrSupportRecordForm, GoProRentalRecordForm, XrBulkItemForm, XrRentalRecordForm

def vr_section(request):
    """VR 設備專區 (統一模型版)"""
    selected_statuses = request.GET.getlist('status')
    vr_items = XrEquipment.objects.filter(section='vr').select_related('category')
    
    if selected_statuses:
        vr_items = vr_items.filter(status__in=selected_statuses)
    
    # 數量統計項目 (配件)
    vr_bulk_items = XrBulkItem.objects.filter(section='vr')
    
    # 分類指取
    context = {
        'vr_computers': vr_items.filter(models.Q(name__icontains='電腦') | models.Q(category__name__icontains='電腦')),
        'vr_headsets': vr_items.filter(models.Q(name__icontains='頭盔') | models.Q(category__name__icontains='頭盔')),
        'vr_others': vr_items.exclude(
            models.Q(name__icontains='電腦') | models.Q(category__name__icontains='電腦') |
            models.Q(name__icontains='頭盔') | models.Q(category__name__icontains='頭盔')
        ),
        'vr_bulk_items': vr_bulk_items,
        'categories': EquipmentCategory.objects.all(),
        'eq_form': XrEquipmentForm(),
        'bulk_form': XrBulkItemForm(),
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
    
    # 數量統計項目 (所有周邊配件整合)
    gp_bulk_items = XrBulkItem.objects.filter(section='gopro')
    
    context = {
        'gp_hosts': gp_items.filter(models.Q(name__icontains='主機') | models.Q(category__name__icontains='主機')),
        'gp_bulk_items': gp_bulk_items,
        'categories': EquipmentCategory.objects.all(),
        'eq_form': XrEquipmentForm(),
        'bulk_form': XrBulkItemForm(),
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

def bulk_item_save(request, pk=None):
    """新增或編輯數量統計項目"""
    if pk:
        item = get_object_or_404(XrBulkItem, pk=pk)
    else:
        item = None

    if request.method == 'POST':
        form = XrBulkItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '庫存資料已儲存')
        else:
            messages.error(request, f'儲存失敗: {form.errors}')
    
    return redirect(request.META.get('HTTP_REFERER', 'XrResource:gopro_section'))

def delete_item(request, model_name, pk):
    """刪除物件"""
    models_map = {
        'equipment': XrEquipment,
        'support': XrSupportRecord,
        'rental': GoProRentalRecord,
        'category': EquipmentCategory,
        'bulk': XrBulkItem,
    }
    model = models_map.get(model_name)
    if model:
        item = get_object_or_404(model, pk=pk)
        item.delete()
        messages.success(request, '刪除成功')
    return redirect(request.META.get('HTTP_REFERER', 'XrResource:dashboard'))

def rental_register(request):
    """租借設備登記頁面"""
    if request.method == 'POST':
        form = XrRentalRecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                rental_record = form.save()
                
                # 1. 處理主機設備狀態連動 (預約中)
                for equipment in rental_record.equipments.all():
                    equipment.status = 'reserved'
                    equipment.save()

                # 2. 處理配件待扣數量連動
                bulk_ids = request.POST.getlist('bulk_item_ids[]')
                bulk_counts = request.POST.getlist('bulk_item_counts[]')
                
                for b_id, b_count in zip(bulk_ids, bulk_counts):
                    if b_id and b_count:
                        count = int(b_count)
                        bulk_item = XrBulkItem.objects.select_for_update().get(id=b_id)
                        
                        # 增加待扣數量 (先不扣在庫)
                        bulk_item.reserved_count += count
                        bulk_item.save()

                        # 建立關連紀錄
                        XrRentalBulkItem.objects.create(
                            rental_record=rental_record,
                            bulk_item=bulk_item,
                            count=count
                        )
                
            messages.success(request, '租借申請已送出！設備已改為「預約中」且配件已標記「待扣」。請等待管理員核准。')
            return redirect('XrResource:rental_list')
        else:
            messages.error(request, '提交失敗，請檢查內容')
    else:
        form = XrRentalRecordForm()
    
    return render(request, 'XrResource/rental_register.html', {
        'form': form,
        'bulk_item_choices': XrBulkItem.objects.filter(available_count__gt=0),
    })

def rental_list(request):
    """租借歷史紀錄列表"""
    rentals = XrRentalRecord.objects.all().prefetch_related('equipments', 'xrrentalbulkitem_set__bulk_item')
    return render(request, 'XrResource/rental_list.html', {
        'rentals': rentals,
    })

def rental_approve(request, pk):
    """核准租借申請"""
    rental = get_object_or_404(XrRentalRecord, pk=pk)
    if rental.status != 'pending':
        messages.warning(request, '此申請已被處理過')
        return redirect('XrResource:rental_list')

    with transaction.atomic():
        # 1. 將單據改為已核准
        rental.status = 'approved'
        rental.save()

        # 2. 將主機轉為已出借
        for eq in rental.equipments.all():
            eq.status = 'rented'
            eq.save()

        # 3. 正式從庫存扣除配件數量 & 清空待扣
        for r_bulk in rental.xrrentalbulkitem_set.all():
            bulk_item = r_bulk.bulk_item
            bulk_item.available_count = max(0, bulk_item.available_count - r_bulk.count)
            bulk_item.reserved_count = max(0, bulk_item.reserved_count - r_bulk.count)
            bulk_item.save()

    messages.success(request, f'已核准 {rental.activity_name} 的租借，庫存已扣除。')
    return redirect('XrResource:rental_list')

def rental_reject(request, pk):
    """拒絕租借申請"""
    rental = get_object_or_404(XrRentalRecord, pk=pk)
    if rental.status != 'pending':
        messages.warning(request, '此申請已被處理過')
        return redirect('XrResource:rental_list')

    with transaction.atomic():
        # 1. 標記為拒絕
        rental.status = 'rejected'
        rental.save()

        # 2. 回復主機狀態為在庫
        for eq in rental.equipments.all():
            eq.status = 'available'
            eq.save()

        # 3. 回復配件待扣數
        for r_bulk in rental.xrrentalbulkitem_set.all():
            bulk_item = r_bulk.bulk_item
            bulk_item.reserved_count = max(0, bulk_item.reserved_count - r_bulk.count)
            bulk_item.save()

    messages.info(request, f'已拒絕 {rental.activity_name} 的租借，預約狀態已解除。')
    return redirect('XrResource:rental_list')

def rental_reset(request, pk):
    """將已核准或已拒絕的申請重設為待核核"""
    rental = get_object_or_404(XrRentalRecord, pk=pk)
    if rental.status == 'pending':
        return redirect('XrResource:rental_list')

    old_status = rental.status

    with transaction.atomic():
        # 1. 恢復主機狀態為預約中
        for eq in rental.equipments.all():
            eq.status = 'reserved'
            eq.save()

        # 2. 恢復配件待扣數 (如果之前是核准，還要加回在庫)
        for r_bulk in rental.xrrentalbulkitem_set.all():
            bulk_item = r_bulk.bulk_item
            if old_status == 'approved':
                # 加回在庫
                bulk_item.available_count += r_bulk.count
            
            # 不論是從已核准或已拒絕恢復，都要恢復待扣數
            bulk_item.reserved_count += r_bulk.count
            bulk_item.save()

        # 3. 標記為待核核
        rental.status = 'pending'
        rental.save()

    messages.info(request, f'已將 {rental.activity_name} 的狀態重設為帶核核，庫存狀態已同步預約。')
    return redirect('XrResource:rental_list')
