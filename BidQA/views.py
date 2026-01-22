from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.db.models import Q, Count
from django.core.paginator import Paginator
import csv
import io

from .models import Bid, Committee, BidCommittee, Question, BidFile, FileDownloadLog
from .forms import BidForm, CommitteeForm, QuestionForm, CommitteeSelectForm, BidFileForm


# ==================== 標案 Views ====================

@login_required
def bid_list(request):
    """標案列表"""
    bids = Bid.objects.annotate(
        committee_count=Count('bid_committees', distinct=True),
        question_count=Count('bid_committees__questions', distinct=True)
    ).select_related('created_by')
    
    # 搜尋
    q = request.GET.get('q', '').strip()
    if q:
        bids = bids.filter(
            Q(name__icontains=q) | 
            Q(bid_number__icontains=q) |
            Q(description__icontains=q)
        )
    
    # 狀態篩選
    status = request.GET.get('status', '')
    if status:
        bids = bids.filter(status=status)
    
    return render(request, 'BidQA/bid_list.html', {
        'bids': bids,
        'q': q,
        'status': status,
        'status_choices': Bid.STATUS_CHOICES,
    })


@login_required
def bid_detail(request, pk):
    """標案詳情"""
    bid = get_object_or_404(Bid, pk=pk)
    bid_committees = bid.bid_committees.select_related('committee').prefetch_related('questions')
    
    return render(request, 'BidQA/bid_detail.html', {
        'bid': bid,
        'bid_committees': bid_committees,
    })


@login_required
def bid_create(request):
    """新增標案"""
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.created_by = request.user
            bid.save()
            messages.success(request, f'標案「{bid.name}」已建立')
            return redirect('bidqa:bid_detail', pk=bid.pk)
    else:
        form = BidForm()
    
    return render(request, 'BidQA/bid_form.html', {
        'form': form,
        'title': '新增標案',
    })


@login_required
def bid_update(request, pk):
    """編輯標案"""
    bid = get_object_or_404(Bid, pk=pk)
    
    if request.method == 'POST':
        form = BidForm(request.POST, instance=bid)
        if form.is_valid():
            form.save()
            messages.success(request, f'標案「{bid.name}」已更新')
            return redirect('bidqa:bid_detail', pk=bid.pk)
    else:
        form = BidForm(instance=bid)
    
    return render(request, 'BidQA/bid_form.html', {
        'form': form,
        'bid': bid,
        'title': '編輯標案',
    })


@login_required
def bid_delete(request, pk):
    """刪除標案"""
    bid = get_object_or_404(Bid, pk=pk)
    
    if request.method == 'POST':
        name = bid.name
        bid.delete()
        messages.success(request, f'標案「{name}」已刪除')
        return redirect('bidqa:bid_list')
    
    return render(request, 'BidQA/confirm_delete.html', {
        'object': bid,
        'object_name': bid.name,
        'cancel_url': 'bidqa:bid_detail',
    })


# ==================== 委員 Views ====================

@login_required
def committee_list(request):
    """委員列表"""
    committees = Committee.objects.annotate(
        question_count=Count('bid_committees__questions', distinct=True),
        bid_count=Count('bid_committees__bid', distinct=True)
    )
    
    q = request.GET.get('q', '').strip()
    if q:
        committees = committees.filter(
            Q(name__icontains=q) |
            Q(organization__icontains=q) |
            Q(specialty__icontains=q)
        )
    
    return render(request, 'BidQA/committee_list.html', {
        'committees': committees,
        'q': q,
    })


@login_required
def committee_detail(request, pk):
    """委員詳情 - 顯示該委員所有問答"""
    committee = get_object_or_404(Committee, pk=pk)
    bid_committees = committee.bid_committees.select_related('bid').prefetch_related('questions')
    
    return render(request, 'BidQA/committee_detail.html', {
        'committee': committee,
        'bid_committees': bid_committees,
    })


@login_required
def committee_create(request):
    """新增委員"""
    if request.method == 'POST':
        form = CommitteeForm(request.POST)
        if form.is_valid():
            committee = form.save()
            messages.success(request, f'委員「{committee.name}」已建立')
            return redirect('bidqa:committee_list')
    else:
        form = CommitteeForm()
    
    return render(request, 'BidQA/committee_form.html', {
        'form': form,
        'title': '新增評審委員',
    })


@login_required
def committee_update(request, pk):
    """編輯委員"""
    committee = get_object_or_404(Committee, pk=pk)
    
    if request.method == 'POST':
        form = CommitteeForm(request.POST, instance=committee)
        if form.is_valid():
            form.save()
            messages.success(request, f'委員「{committee.name}」已更新')
            return redirect('bidqa:committee_detail', pk=committee.pk)
    else:
        form = CommitteeForm(instance=committee)
    
    return render(request, 'BidQA/committee_form.html', {
        'form': form,
        'committee': committee,
        'title': '編輯評審委員',
    })


# ==================== 標案委員關聯 Views ====================

@login_required
def add_committee_to_bid(request, bid_pk):
    """新增委員到標案"""
    bid = get_object_or_404(Bid, pk=bid_pk)
    
    if request.method == 'POST':
        form = CommitteeSelectForm(request.POST)
        if form.is_valid():
            committee = form.cleaned_data.get('committee')
            new_name = form.cleaned_data.get('new_name')
            
            if new_name:
                # 建立新委員
                committee = Committee.objects.create(
                    name=new_name,
                    organization=form.cleaned_data.get('new_organization', '')
                )
            
            # 建立關聯
            bid_committee, created = BidCommittee.objects.get_or_create(
                bid=bid,
                committee=committee
            )
            
            if created:
                messages.success(request, f'已新增委員「{committee.name}」')
            else:
                messages.warning(request, f'委員「{committee.name}」已在此標案中')
            
            return redirect('bidqa:bid_detail', pk=bid.pk)
    else:
        form = CommitteeSelectForm()
    
    return render(request, 'BidQA/add_committee.html', {
        'form': form,
        'bid': bid,
    })


@login_required
def remove_committee_from_bid(request, bid_pk, committee_pk):
    """從標案移除委員"""
    bid_committee = get_object_or_404(BidCommittee, bid_id=bid_pk, committee_id=committee_pk)
    
    if request.method == 'POST':
        committee_name = bid_committee.committee.name
        bid_committee.delete()
        messages.success(request, f'已移除委員「{committee_name}」')
        return redirect('bidqa:bid_detail', pk=bid_pk)
    
    return render(request, 'BidQA/confirm_delete.html', {
        'object': bid_committee,
        'object_name': f'{bid_committee.bid.name} - {bid_committee.committee.name}',
        'cancel_url': 'bidqa:bid_detail',
        'cancel_pk': bid_pk,
    })


# ==================== 問答 Views ====================

@login_required
def question_create(request, bid_committee_pk):
    """新增問答"""
    bid_committee = get_object_or_404(
        BidCommittee.objects.select_related('bid', 'committee'),
        pk=bid_committee_pk
    )
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.bid_committee = bid_committee
            question.save()
            messages.success(request, '問答記錄已新增')
            return redirect('bidqa:bid_detail', pk=bid_committee.bid.pk)
    else:
        # 設定預設排序
        next_order = bid_committee.questions.count() + 1
        form = QuestionForm(initial={'order': next_order})
    
    return render(request, 'BidQA/question_form.html', {
        'form': form,
        'bid_committee': bid_committee,
        'title': '新增問答記錄',
    })


@login_required
def question_update(request, pk):
    """編輯問答"""
    question = get_object_or_404(
        Question.objects.select_related('bid_committee__bid', 'bid_committee__committee'),
        pk=pk
    )
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, '問答記錄已更新')
            return redirect('bidqa:bid_detail', pk=question.bid_committee.bid.pk)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'BidQA/question_form.html', {
        'form': form,
        'question': question,
        'bid_committee': question.bid_committee,
        'title': '編輯問答記錄',
    })


@login_required
def question_delete(request, pk):
    """刪除問答"""
    question = get_object_or_404(
        Question.objects.select_related('bid_committee__bid'),
        pk=pk
    )
    bid_pk = question.bid_committee.bid.pk
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, '問答記錄已刪除')
        return redirect('bidqa:bid_detail', pk=bid_pk)
    
    return render(request, 'BidQA/confirm_delete.html', {
        'object': question,
        'object_name': str(question),
        'cancel_url': 'bidqa:bid_detail',
        'cancel_pk': bid_pk,
    })


# ==================== 快速查詢 ====================

@login_required
def quick_search(request):
    """快速查詢 - 依委員名稱、提問、回答內容搜尋問答"""
    q = request.GET.get('q', '').strip()
    results = []
    seen_questions = set()  # 避免重複結果
    
    if q:
        # 方法1: 搜尋委員名稱/單位
        committees = Committee.objects.filter(
            Q(name__icontains=q) | Q(organization__icontains=q)
        ).prefetch_related(
            'bid_committees__bid',
            'bid_committees__questions'
        )
        
        for committee in committees:
            for bc in committee.bid_committees.all():
                for question in bc.questions.all():
                    if question.pk not in seen_questions:
                        seen_questions.add(question.pk)
                        results.append({
                            'committee': committee,
                            'bid': bc.bid,
                            'question': question,
                            'match_type': 'committee',
                        })
        
        # 方法2: 搜尋問答內容
        questions = Question.objects.filter(
            Q(question__icontains=q) | 
            Q(answer__icontains=q) | 
            Q(reference__icontains=q)
        ).select_related(
            'bid_committee__bid',
            'bid_committee__committee'
        )
        
        for question in questions:
            if question.pk not in seen_questions:
                seen_questions.add(question.pk)
                results.append({
                    'committee': question.bid_committee.committee,
                    'bid': question.bid_committee.bid,
                    'question': question,
                    'match_type': 'content',
                })
    
    return render(request, 'BidQA/quick_search.html', {
        'q': q,
        'results': results,
        'result_count': len(results),
    })


# ==================== API ====================

@login_required
def search_committees_api(request):
    """搜尋委員 API"""
    q = request.GET.get('q', '').strip()
    
    if len(q) < 2:
        return JsonResponse({'committees': []})
    
    committees = Committee.objects.filter(
        Q(name__icontains=q) | Q(organization__icontains=q)
    )[:10]
    
    return JsonResponse({
        'committees': [
            {
                'id': c.id,
                'name': c.name,
                'organization': c.organization,
                'display': str(c),
            }
            for c in committees
        ]
    })


@login_required
def search_committees_by_name_api(request):
    """搜尋同名委員 API - 用於新增委員時的智慧建議"""
    name = request.GET.get('name', '').strip()
    
    if len(name) < 1:
        return JsonResponse({'committees': []})
    
    # 完全符合姓名的優先
    exact_match = Committee.objects.filter(name=name).annotate(
        question_count=Count('bid_committees__questions', distinct=True)
    )
    
    # 部分符合的
    partial_match = Committee.objects.filter(
        name__icontains=name
    ).exclude(
        name=name
    ).annotate(
        question_count=Count('bid_committees__questions', distinct=True)
    )[:5]
    
    committees = list(exact_match) + list(partial_match)
    
    return JsonResponse({
        'committees': [
            {
                'id': c.id,
                'name': c.name,
                'organization': c.organization or '',
                'specialty': c.specialty or '',
                'notes': (c.notes[:100] + '...' if c.notes and len(c.notes) > 100 else c.notes) or '',
                'question_count': c.question_count,
                'display': str(c),
                'exact_match': c.name == name,
            }
            for c in committees
        ]
    })


@login_required
def import_committees(request):
    """匯入委員 CSV"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, '請選擇 CSV 檔案')
            return redirect('bidqa:import_committees')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '請上傳 CSV 格式檔案')
            return redirect('bidqa:import_committees')
        
        try:
            # 讀取 CSV 內容
            content = csv_file.read().decode('utf-8-sig')  # 處理 BOM
            reader = csv.reader(io.StringIO(content))
            
            created_count = 0
            skipped_count = 0
            
            for row in reader:
                if len(row) < 3:
                    continue
                
                # CSV 格式: 序號, 姓名, 單位/職稱, 經歷/學歷, ...
                try:
                    name = row[1].strip()
                    organization = row[2].strip()
                    notes = row[3].strip() if len(row) > 3 else ''
                except (IndexError, AttributeError):
                    continue
                
                if not name:
                    continue
                
                # 檢查是否已存在同姓名同單位的委員
                exists = Committee.objects.filter(
                    name=name,
                    organization=organization
                ).exists()
                
                if exists:
                    skipped_count += 1
                else:
                    Committee.objects.create(
                        name=name,
                        organization=organization,
                        notes=notes
                    )
                    created_count += 1
            
            messages.success(
                request, 
                f'匯入完成！新增 {created_count} 位委員，略過 {skipped_count} 位（已存在）'
            )
            return redirect('bidqa:committee_list')
            
        except Exception as e:
            messages.error(request, f'匯入失敗：{str(e)}')
            return redirect('bidqa:import_committees')
    
    return render(request, 'BidQA/import_committees.html')


# ==================== 檔案 Views ====================

def get_client_ip(request):
    """取得客戶端 IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def file_upload(request, bid_pk):
    """上傳檔案到標案"""
    bid = get_object_or_404(Bid, pk=bid_pk)
    
    if request.method == 'POST':
        form = BidFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            bid_file = BidFile.objects.create(
                bid=bid,
                file=uploaded_file,
                filename=uploaded_file.name,
                description=form.cleaned_data.get('description', ''),
                uploaded_by=request.user
            )
            messages.success(request, f'檔案「{bid_file.filename}」上傳成功')
            return redirect('bidqa:bid_detail', pk=bid.pk)
    else:
        form = BidFileForm()
    
    return render(request, 'BidQA/file_upload.html', {
        'form': form,
        'bid': bid,
    })


@login_required
def file_download(request, pk):
    """下載檔案並記錄"""
    bid_file = get_object_or_404(BidFile, pk=pk)
    
    # 記錄下載
    FileDownloadLog.objects.create(
        file=bid_file,
        downloaded_by=request.user,
        ip_address=get_client_ip(request)
    )
    
    # 回傳檔案
    try:
        response = FileResponse(
            bid_file.file.open('rb'),
            as_attachment=True,
            filename=bid_file.filename
        )
        return response
    except FileNotFoundError:
        raise Http404("檔案不存在")


@login_required
def file_delete(request, pk):
    """刪除檔案"""
    bid_file = get_object_or_404(BidFile, pk=pk)
    bid_pk = bid_file.bid.pk
    
    if request.method == 'POST':
        filename = bid_file.filename
        bid_file.file.delete()  # 刪除實體檔案
        bid_file.delete()
        messages.success(request, f'檔案「{filename}」已刪除')
        return redirect('bidqa:bid_detail', pk=bid_pk)
    
    return render(request, 'BidQA/confirm_delete.html', {
        'object': bid_file,
        'object_name': bid_file.filename,
        'cancel_url': 'bidqa:bid_detail',
        'cancel_pk': bid_pk,
    })


@login_required
def file_download_logs(request, pk):
    """查看檔案下載記錄"""
    bid_file = get_object_or_404(BidFile, pk=pk)
    logs = bid_file.downloads.select_related('downloaded_by').all()
    
    return render(request, 'BidQA/file_download_logs.html', {
        'file': bid_file,
        'logs': logs,
    })


