from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from decimal import Decimal
from .models import Expense, ExpenseSplit, Participant


def get_statistics(period='all', start_date=None, end_date=None):
    """
    取得統計資料
    period: 'day', 'week', 'month', 'all'
    """
    today = timezone.now().date()
    
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    
    queryset = Expense.objects.all()
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    # 總支出
    total_amount = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # 各類型支出
    category_stats = queryset.values(
        'category__name', 'category__color'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # 計算百分比
    category_data = []
    for stat in category_stats:
        percentage = (stat['total'] / total_amount * 100) if total_amount > 0 else 0
        category_data.append({
            'name': stat['category__name'] or '未分類',
            'color': stat['category__color'] or '#6c757d',
            'total': float(stat['total']),
            'percentage': round(float(percentage), 1)
        })
    
    return {
        'total_amount': float(total_amount),
        'category_data': category_data,
        'expense_count': queryset.count(),
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
    }


def calculate_settlement():
    """
    計算分帳結算結果
    返回「誰欠誰多少錢」的清單
    """
    # 計算每個人應付的總額（他們的分攤）
    participants = Participant.objects.filter(is_active=True)
    
    # 每個人的收支平衡
    balance = defaultdict(Decimal)
    
    for participant in participants:
        # 他付的錢
        paid = Expense.objects.filter(
            paid_by=participant
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # 他應分攤的錢
        owed = ExpenseSplit.objects.filter(
            participant=participant
        ).aggregate(total=Sum('share_amount'))['total'] or Decimal('0')
        
        # 正數表示別人欠他錢，負數表示他欠別人錢
        balance[participant.id] = paid - owed
    
    # 簡化債務關係
    settlements = []
    creditors = [(pid, bal) for pid, bal in balance.items() if bal > 0]
    debtors = [(pid, -bal) for pid, bal in balance.items() if bal < 0]
    
    # 排序以便快速配對
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    
    participant_map = {p.id: p.name for p in participants}
    
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        creditor_id, credit = creditors[i]
        debtor_id, debt = debtors[j]
        
        amount = min(credit, debt)
        if amount > Decimal('0.01'):  # 忽略極小金額
            settlements.append({
                'from_name': participant_map.get(debtor_id, '未知'),
                'to_name': participant_map.get(creditor_id, '未知'),
                'amount': float(amount.quantize(Decimal('0.01')))
            })
        
        creditors[i] = (creditor_id, credit - amount)
        debtors[j] = (debtor_id, debt - amount)
        
        if creditors[i][1] <= Decimal('0.01'):
            i += 1
        if debtors[j][1] <= Decimal('0.01'):
            j += 1
    
    return settlements


def get_participant_summary():
    """取得每位參與者的收支摘要"""
    participants = Participant.objects.filter(is_active=True)
    summaries = []
    
    for participant in participants:
        paid = Expense.objects.filter(
            paid_by=participant
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        owed = ExpenseSplit.objects.filter(
            participant=participant
        ).aggregate(total=Sum('share_amount'))['total'] or Decimal('0')
        
        balance = paid - owed
        
        summaries.append({
            'id': participant.id,
            'name': participant.name,
            'paid': float(paid),
            'owed': float(owed),
            'balance': float(balance),
        })
    
    return summaries
