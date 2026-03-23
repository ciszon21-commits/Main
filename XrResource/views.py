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
    
    # 分類指取 (僅依據類別名稱)
    context = {
        'vr_computers': vr_items.filter(category__name='電腦'),
        'vr_headsets': vr_items.filter(category__name='頭盔'),
        'vr_others': vr_items.exclude(category__name__in=['電腦', '頭盔']),
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
        'gp_hosts': gp_items.filter(category__name='主機'),
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
def rental_register(request, pk=None):
    """租借設備登記與編輯頁面"""
    rental = None
    if pk:
        rental = get_object_or_404(XrRentalRecord, pk=pk)
        # 僅限管理員編輯，或使用者編輯自己的待核准單據 (目前依要求主要供管理員調整)
        is_admin = request.user.xr_profile.role == 'admin'
        if not (is_admin or rental.borrower_id == request.user.username):
            messages.error(request, '您沒有權限編輯此申請。')
            return redirect('XrResource:rental_list')
        
        # 僅管理員可以編輯非「待核准」狀態的紀錄
        if not is_admin and rental.status != 'pending':
            messages.warning(request, '僅能修改「待核准」狀態的申請紀錄。')
            return redirect('XrResource:rental_list')

    if request.method == 'POST':
        form = XrRentalRecordForm(request.POST, instance=rental)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 如果是編輯模式，且原本是「待核准」才需要進行庫存還原邏輯
                    # 對於「已歸還」等歷史資料，編輯時我們不自動變動庫存狀態
                    is_pending = rental and rental.status == 'pending'
                    if is_pending:
                        # 1. 恢復主機設備為可用
                        for eq in rental.equipments.all():
                            eq.update_status(exclude_ids=[rental.id])
                        # 2. 恢復配件預約數
                        for r_bulk in rental.xrrentalbulkitem_set.all():
                            bulk_item = r_bulk.bulk_item
                            bulk_item.reserved_count = max(0, bulk_item.reserved_count - r_bulk.count)
                            bulk_item.save()
                        # 刪除舊的配件關聯
                        rental.xrrentalbulkitem_set.all().delete()

                    # 儲存主要單據
                    rental_record = form.save()
                    
                    # 只有在「待核准」或「新申請」時，才套用預約邏輯
                    # 歷史資料 (returned) 編輯不更動庫存狀態
                    if not rental or rental.status == 'pending':
                        # 1. 主機設備改為預約中
                        for equipment in rental_record.equipments.all():
                            equipment.update_status()

                    # 2. 處理配件待扣數量 (不論是否 pending 都要建立關聯，但只有 pending 會加 reserved_count)
                    bulk_ids = request.POST.getlist('bulk_item_ids[]')
                    bulk_counts = request.POST.getlist('bulk_item_counts[]')
                    
                    for b_id, b_count in zip(bulk_ids, bulk_counts):
                        if b_id and b_count:
                            count = int(b_count)
                            bulk_item = XrBulkItem.objects.select_for_update().get(id=b_id)
                            
                            if not rental or rental.status == 'pending':
                                # 增加新的待扣數量
                                bulk_item.reserved_count += count
                                bulk_item.save()

                            # 重新建立關連
                            XrRentalBulkItem.objects.create(
                                rental_record=rental_record,
                                bulk_item=bulk_item,
                                count=count,
                                is_returned=(rental and rental.status == 'returned') # 歷史資料預設設為已歸還
                            )
                
                msg = '租借申請已更新！' if rental else '租借申請已送出！'
                messages.success(request, f'{msg}設備已改為「預約」且配件已標記「待扣」。')
                return redirect('XrResource:rental_list')
            except IntegrityError:
                messages.error(request, '調整失敗：更新過程中發生數據衝突，請稍後再試。')
        else:
            messages.error(request, '提交失敗，請檢查填寫內容。')
    else:
        form = XrRentalRecordForm(instance=rental)
    
    # 獲取已選配件供編輯顯示
    existing_bulk_items = []
    if rental:
        existing_bulk_items = rental.xrrentalbulkitem_set.all()

    return render(request, 'XrResource/rental_register.html', {
        'form': form,
        'rental': rental,
        'existing_bulk_items': existing_bulk_items,
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
            eq.update_status()

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
            eq.update_status()

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
                eq.update_status()

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
                eq.update_status()

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
        # 獲取勾選要歸還的 ID 與備註
        returned_equipment_ids = request.POST.getlist('returned_equipments')
        returned_bulk_item_ids = request.POST.getlist('returned_bulk_items')
        return_notes = request.POST.get('return_notes', '')
        
        with transaction.atomic():
            # 1. 保存歸還備註
            rental.return_notes = return_notes
            rental.save()
            
            # 2. 處理主機歸還
            for eq_id in returned_equipment_ids:
                equipment = rental.equipments.get(id=eq_id)
                if equipment.status == 'rented':
                    # 歸還後檢查是否有其他單子預約/出借，排除當前這張單
                    equipment.update_status(exclude_ids=[rental.id])
            
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
    
    return render(request, 'XrResource/rental_return.html', {
        'rental': rental,
        'bulk_items': rental.xrrentalbulkitem_set.all(),
    })

@login_required
def dashboard(request):
    """視覺化儀表板：提供設備在庫與預約概況"""
    def get_stats(query):
        total = query.count()
        available = query.filter(status='available').count()
        reserved = query.filter(status='reserved').count()
        rented = query.filter(status='rented').count()
        return {
            'total': total,
            'available': available,
            'reserved': reserved,
            'rented': rented,
            'unavailable': total - available,
            'available_pct': int((available / total * 100)) if total > 0 else 0
        }

    # 1. 分類統計 (只統計 庫存、預約、出借)
    # VR 電腦
    vr_comp_q = XrEquipment.objects.filter(section='vr', category__name='電腦', status__in=['available', 'reserved', 'rented'])
    vr_comp_stats = get_stats(vr_comp_q)
    
    # VR 頭盔
    vr_headset_q = XrEquipment.objects.filter(section='vr', category__name='頭盔', status__in=['available', 'reserved', 'rented'])
    vr_headset_stats = get_stats(vr_headset_q)
    
    # 攝影設備-主機 (GoPro 主機)
    camera_host_q = XrEquipment.objects.filter(section='gopro', category__name='主機', status__in=['available', 'reserved', 'rented'])
    camera_host_stats = get_stats(camera_host_q)

    # 2. 配件統計 (不分專區)
    bulk_items = XrBulkItem.objects.all()
    
    # 3. 最近活動 (最新的 10 筆租借申請)
    recent_rentals = XrRentalRecord.objects.all().order_by('-created_at')[:10]

    return render(request, 'XrResource/dashboard.html', {
        'vr_comp_stats': vr_comp_stats,
        'vr_headset_stats': vr_headset_stats,
        'camera_host_stats': camera_host_stats,
        'bulk_items': bulk_items,
        'recent_rentals': recent_rentals,
    })
