from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models, transaction, IntegrityError
from .models import EquipmentCategory, XrEquipment, XrSupportRecord, GoProRentalRecord, XrBulkItem, XrRentalRecord, XrRentalBulkItem, XrUserProfile
from .forms import EquipmentCategoryForm, XrEquipmentForm, XrSupportRecordForm, GoProRentalRecordForm, XrBulkItemForm, XrRentalRecordForm
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if hasattr(request.user, 'xr_profile') and request.user.xr_profile.role == 'admin':
            return view_func(request, *args, **kwargs)
        messages.warning(request, '您沒有權限執行此操作或進入此頁面。')
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('XrResource:vr_section')
    return _wrapped_view

@login_required
@admin_required
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

@login_required
@admin_required
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

@login_required
@admin_required
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

@login_required
@admin_required
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

@login_required
@admin_required
def delete_item(request, model_name, pk):
    """刪除物件"""
    models_map = {
        'equipment': XrEquipment,
        'support': XrSupportRecord,
        'rental': XrRentalRecord,
        'category': EquipmentCategory,
        'bulk': XrBulkItem,
    }
    model = models_map.get(model_name)
    if model:
        item = get_object_or_404(model, pk=pk)
        item.delete()
        messages.success(request, '刪除成功')
    return redirect(request.META.get('HTTP_REFERER', 'XrResource:dashboard'))

@login_required
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
                        
                        # 增加待扣數量 (先不扣除庫存)
                        bulk_item.reserved_count += count
                        bulk_item.save()

                        # 建立關連紀錄
                        XrRentalBulkItem.objects.create(
                            rental_record=rental_record,
                            bulk_item=bulk_item,
                            count=count
                        )
                
            messages.success(request, '租借申請已送出！設備已改為「預約」且配件已標記「待扣」。請等待管理員核准。')
            return redirect('XrResource:rental_list')
        else:
            messages.error(request, '提交失敗，請檢查內容')
    else:
        form = XrRentalRecordForm()
    
    return render(request, 'XrResource/rental_register.html', {
        'form': form,
        'bulk_item_choices': XrBulkItem.objects.filter(available_count__gt=0),
    })

@login_required
def rental_list(request):
    """租借歷史紀錄列表"""
    rentals = XrRentalRecord.objects.all().prefetch_related('equipments', 'xrrentalbulkitem_set__bulk_item')
    return render(request, 'XrResource/rental_list.html', {
        'rentals': rentals,
    })

@login_required
@admin_required
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

@login_required
@admin_required
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

        # 2. 回復主機狀態為庫存
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

@login_required
@admin_required
def rental_reset(request, pk):
    """將已核准、已拒絕或已歸還的申請重設為待核准"""
    rental = get_object_or_404(XrRentalRecord, pk=pk)
    if rental.status == 'pending':
        return redirect('XrResource:rental_list')

    old_status = rental.status

    try:
        with transaction.atomic():
            # 1. 恢復主機狀態為預約中
            for eq in rental.equipments.all():
                eq.status = 'reserved'
                eq.save()

            # 2. 恢復配件數據
            for r_bulk in rental.xrrentalbulkitem_set.all():
                bulk_item = r_bulk.bulk_item
                
                # 只有當原本是「已核准」且「該項目尚未歸還」時，才需要加回在庫。
                # 如果是「已歸還」狀態，在庫早就在歸還點交時加回了，不可再扣除或重複加。
                # 如果是「已拒絕」狀態，當時根本沒扣在庫，也不動。
                if old_status == 'approved' and not r_bulk.is_returned:
                    bulk_item.available_count += r_bulk.count
                
                # 不論是從哪種狀態(核准/拒絕/歸還)恢復為待核准，都要加回「待扣數量 (Reserved)」
                bulk_item.reserved_count += r_bulk.count
                bulk_item.save()
                
                # 重設配件項目的個別歸還狀態
                r_bulk.is_returned = False
                r_bulk.save()

            # 3. 標記為待核准
            rental.status = 'pending'
            rental.save()
            
        messages.info(request, f'已將 {rental.activity_name} 的狀態重設為待核准，其所屬設備已回歸庫存預約狀態。')
    except IntegrityError:
        messages.error(request, '重設失敗：庫存數量不足以回歸預約狀態。請檢查是否有其他單據已佔用庫存。')
    
    return redirect('XrResource:rental_list')

@login_required
@admin_required
def reset_rental_return(request, pk):
    """初始化點交紀錄：將歸還狀態設回借用中，並維持訂單為已核准狀態"""
    rental = get_object_or_404(XrRentalRecord, pk=pk)
    
    # 只有已核准或已歸還的單據可以初始化點交紀錄
    if rental.status not in ['approved', 'returned']:
        messages.warning(request, '此狀態下無法初始化點交紀錄。')
        return redirect('XrResource:rental_return', pk=pk)

    try:
        with transaction.atomic():
            # 1. 將所有關連的主機設回「借用中」
            for eq in rental.equipments.all():
                if eq.status == 'available':  # 表示之前已歸還
                    eq.status = 'rented'
                    eq.save()

            # 2. 將所有配件設回「未歸還」，並扣除庫存
            for r_bulk in rental.xrrentalbulkitem_set.all():
                if r_bulk.is_returned:
                    bulk_item = r_bulk.bulk_item
                    # 撤回歸還：庫存要減掉
                    bulk_item.available_count -= r_bulk.count
                    bulk_item.save()
                    
                    r_bulk.is_returned = False
                    r_bulk.save()

            # 3. 強制將單據狀態設回「已核准」
            rental.status = 'approved'
            rental.save()
            
        messages.success(request, f'已成功初始化 {rental.activity_name} 的點交紀錄。')
    except IntegrityError:
        messages.error(request, '重設失敗：庫存數量不足以回歸借用狀態。')
    
    return redirect('XrResource:rental_return', pk=pk)

@login_required
@admin_required
def rental_return(request, pk):
    """處理設備歸還確認頁面與邏輯"""
    rental = get_object_or_404(XrRentalRecord, pk=pk)
    
    if request.method == 'POST':
        # 獲取勾選要歸還的 ID
        returned_equipment_ids = request.POST.getlist('returned_equipments')
        returned_bulk_item_ids = request.POST.getlist('returned_bulk_items')
        
        with transaction.atomic():
            # 1. 處理主機歸還
            for eq_id in returned_equipment_ids:
                equipment = rental.equipments.get(id=eq_id)
                if equipment.status == 'rented':
                    equipment.status = 'available'
                    equipment.save()
            
            # 2. 處理配件歸還
            for rb_id in returned_bulk_item_ids:
                r_bulk = rental.xrrentalbulkitem_set.get(id=rb_id)
                if not r_bulk.is_returned:
                    # 正式補回庫存
                    bulk_item = r_bulk.bulk_item
                    bulk_item.available_count += r_bulk.count
                    bulk_item.save()
                    
                    # 標記該項目已歸還
                    r_bulk.is_returned = True
                    r_bulk.save()
            
            # 3. 檢查自動關單 (是否所有東西都還了)
            all_eq_returned = not rental.equipments.filter(status='rented').exists()
            all_bulk_returned = not rental.xrrentalbulkitem_set.filter(is_returned=False).exists()
            
            if all_eq_returned and all_bulk_returned:
                rental.status = 'returned'
                rental.save()
                messages.success(request, f'{rental.activity_name} 所有設備已歸還，單據已結案。')
            else:
                messages.info(request, f'{rental.activity_name} 部分設備已歸還。')
                
        return redirect('XrResource:rental_list')
    
    # GET 請求：顯示歸還表單
    return render(request, 'XrResource/rental_return.html', {
        'rental': rental,
        'bulk_items': rental.xrrentalbulkitem_set.all(),
    })
