from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import csv

from .models import Expense, ExpenseCategory, Participant, ExpenseSplit
from .forms import ExpenseForm, CategoryForm, ParticipantForm, ExpenseFilterForm
from .services import get_statistics, calculate_settlement, get_participant_summary


def expense_list(request):
    """記帳列表"""
    filter_form = ExpenseFilterForm(request.GET)
    queryset = Expense.objects.select_related('category', 'paid_by')
    
    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        category = filter_form.cleaned_data.get('category')
        keyword = filter_form.cleaned_data.get('keyword')
        sort_by = filter_form.cleaned_data.get('sort_by') or '-date'
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if category:
            queryset = queryset.filter(category=category)
        if keyword:
            queryset = queryset.filter(
                Q(item_name__icontains=keyword) | Q(note__icontains=keyword)
            )
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by('-date', '-time')
    
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
    }
    return render(request, 'badminton/expense_list.html', context)


def expense_create(request):
    """新增記帳"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()
            
            # 處理分攤
            split_participants = form.cleaned_data.get('split_participants')
            if split_participants:
                share_amount = expense.amount / len(split_participants)
                for participant in split_participants:
                    ExpenseSplit.objects.create(
                        expense=expense,
                        participant=participant,
                        share_amount=share_amount
                    )
            
            messages.success(request, f'已新增記帳:{expense.item_name}')
            return redirect('badminton:expense_list')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form,
        'title': '新增記帳',
    }
    return render(request, 'badminton/expense_form.html', context)


def expense_update(request, pk):
    """編輯記帳"""
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            # Retain original date and time if not provided
            if not form.cleaned_data.get('date'):
                form.instance.date = expense.date
            if not form.cleaned_data.get('time'):
                form.instance.time = expense.time

            expense = form.save()

            # 更新分攤
            ExpenseSplit.objects.filter(expense=expense).delete()
            split_participants = form.cleaned_data.get('split_participants')
            if split_participants:
                share_amount = expense.amount / len(split_participants)
                for participant in split_participants:
                    ExpenseSplit.objects.create(
                        expense=expense,
                        participant=participant,
                        share_amount=share_amount
                    )

            messages.success(request, f'已更新記帳:{expense.item_name}')
            return redirect('badminton:expense_list')
    else:
        form = ExpenseForm(instance=expense)
        # 預設勾選已分攤的參與者
        existing_splits = ExpenseSplit.objects.filter(expense=expense).values_list('participant_id', flat=True)
        form.fields['split_participants'].initial = list(existing_splits)
    
    context = {
        'form': form,
        'expense': expense,
        'title': '編輯記帳',
    }
    return render(request, 'badminton/expense_form.html', context)


def expense_delete(request, pk):
    """刪除記帳"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        item_name = expense.item_name
        expense.delete()
        messages.success(request, f'已刪除記帳:{item_name}')
        return redirect('badminton:expense_list')
    
    context = {
        'expense': expense,
    }
    return render(request, 'badminton/expense_confirm_delete.html', context)


def dashboard(request):
    """統計儀表板"""
    period = request.GET.get('period', 'all')
    stats = get_statistics(period=period)
    
    context = {
        'stats': stats,
        'current_period': period,
    }
    return render(request, 'badminton/dashboard.html', context)


def dashboard_api(request):
    """統計資料 API"""
    period = request.GET.get('period', 'all')
    stats = get_statistics(period=period)
    return JsonResponse(stats)


def settlement(request):
    """分帳結算"""
    settlements = calculate_settlement()
    summaries = get_participant_summary()
    
    context = {
        'settlements': settlements,
        'summaries': summaries,
    }
    return render(request, 'badminton/settlement.html', context)


def category_list(request):
    """類型列表"""
    categories = ExpenseCategory.objects.all()
    form = CategoryForm()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '已新增類型')
            return redirect('badminton:category_list')
    
    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'badminton/category_list.html', context)


def category_edit(request, pk):
    """編輯類型"""
    category = get_object_or_404(ExpenseCategory, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'已更新類型:{category.name}')
            return redirect('badminton:category_list')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'title': '編輯類型',
    }
    return render(request, 'badminton/category_form.html', context)


def category_delete(request, pk):
    """刪除類型"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, '已刪除類型')
    return redirect('badminton:category_list')


def participant_list(request):
    """參與者列表"""
    participants = Participant.objects.all()
    form = ParticipantForm()
    
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '已新增參與者')
            return redirect('badminton:participant_list')
    
    context = {
        'participants': participants,
        'form': form,
    }
    return render(request, 'badminton/participant_list.html', context)


def participant_delete(request, pk):
    """刪除參與者"""
    participant = get_object_or_404(Participant, pk=pk)
    if request.method == 'POST':
        participant.delete()
        messages.success(request, '已刪除參與者')
    return redirect('badminton:participant_list')


def export_expenses_csv(request):
    """Export expenses as a CSV file."""
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Item Name', 'Category', 'Amount', 'Paid By', 'Note'])

    expenses = Expense.objects.select_related('category', 'paid_by').all()
    for expense in expenses:
        writer.writerow([
            expense.date,
            expense.time,
            expense.item_name,
            expense.category.name if expense.category else '',
            expense.amount,
            expense.paid_by.name if expense.paid_by else '',
            expense.note
        ])

    return response
