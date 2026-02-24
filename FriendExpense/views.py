from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from django.db.models import Sum

from .models import ExpenseGroup, Member, Expense, ExpenseSplit, ExpenseCategory, ExpenseItem
from .forms import ExpenseGroupForm, MemberForm, ExpenseForm


class GroupListView(LoginRequiredMixin, ListView):
    """群組列表"""
    model = ExpenseGroup
    template_name = 'FriendExpense/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return ExpenseGroup.objects.filter(
            created_by=self.request.user
        ).prefetch_related('members', 'expenses')


class GroupCreateView(LoginRequiredMixin, CreateView):
    """建立群組"""
    model = ExpenseGroup
    form_class = ExpenseGroupForm
    template_name = 'FriendExpense/group_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '群組建立成功！')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('friend_expense:group_detail', kwargs={'pk': self.object.pk})


class GroupDetailView(LoginRequiredMixin, DetailView):
    """群組詳情"""
    model = ExpenseGroup
    template_name = 'FriendExpense/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.members.all()
        # 優化查詢：預取 category
        context['expenses'] = self.object.expenses.select_related('paid_by', 'category').prefetch_related('splits__member')[:20]
        context['total_expense'] = self.object.get_total_expense()
        context['member_form'] = MemberForm()
        
        # 計算分類統計
        category_stats = self.object.expenses.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # 處理未分類 (None) 並格式化資料供 Chart.js 使用
        labels = []
        data = []
        formatted_stats = []
        
        for stat in category_stats:
            name = stat['category__name'] or '未分類'
            amount = stat['total']
            labels.append(name)
            data.append(float(amount))
            formatted_stats.append({'name': name, 'total': amount})
            
        context['category_stats'] = formatted_stats
        context['chart_labels'] = labels
        context['chart_data'] = data
        
        return context


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    """更新群組"""
    model = ExpenseGroup
    form_class = ExpenseGroupForm
    template_name = 'FriendExpense/group_form.html'

    def get_success_url(self):
        messages.success(self.request, '群組更新成功！')
        return reverse('friend_expense:group_detail', kwargs={'pk': self.object.pk})


class GroupDeleteView(LoginRequiredMixin, DeleteView):
    """刪除群組"""
    model = ExpenseGroup
    template_name = 'FriendExpense/group_confirm_delete.html'
    success_url = reverse_lazy('friend_expense:group_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '群組已刪除！')
        return super().delete(request, *args, **kwargs)


class MemberAddView(LoginRequiredMixin, View):
    """加入成員"""
    def post(self, request, group_pk):
        group = get_object_or_404(ExpenseGroup, pk=group_pk)
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.group = group
            member.save()
            messages.success(request, f'成員 {member.name} 已加入！')
        else:
            messages.error(request, '加入成員失敗！')
        return redirect('friend_expense:group_detail', pk=group_pk)


class MemberDeleteView(LoginRequiredMixin, View):
    """移除成員"""
    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        group_pk = member.group.pk
        name = member.name
        member.delete()
        messages.success(request, f'成員 {name} 已移除！')
        return redirect('friend_expense:group_detail', pk=group_pk)


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """新增消費記錄"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'FriendExpense/expense_form.html'

    def get_group(self):
        return get_object_or_404(ExpenseGroup, pk=self.kwargs['group_pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['group'] = self.get_group()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.get_group()
        return context

    def form_valid(self, form):
        group = self.get_group()
        form.instance.group = group
        self.object = form.save()

        # 處理消費細項
        item_names = self.request.POST.getlist('item_names[]')
        item_amounts = self.request.POST.getlist('item_amounts[]')
        
        if item_names and item_amounts:
            for name, amount in zip(item_names, item_amounts):
                if name.strip() and amount:
                    ExpenseItem.objects.create(
                        expense=self.object,
                        name=name.strip(),
                        amount=amount
                    )

        # 處理分帳
        split_members = form.cleaned_data['split_members']
        split_equally = form.cleaned_data['split_equally']

        if split_equally and split_members:
            # 平均分攤
            split_amount = self.object.amount / len(split_members)
            for member in split_members:
                ExpenseSplit.objects.create(
                    expense=self.object,
                    member=member,
                    amount=split_amount
                )

        messages.success(self.request, '記帳成功！')
        return redirect('friend_expense:group_detail', pk=group.pk)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """編輯消費記錄"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'FriendExpense/expense_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['group'] = self.object.group
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.object.group
        # 取得已選擇的分攤成員
        context['form'].fields['split_members'].initial = self.object.splits.values_list('member', flat=True)
        # 取得消費細項
        context['expense_items'] = self.object.items.all()
        return context

    def form_valid(self, form):
        self.object = form.save()

        # 處理消費細項
        # 先刪除舊的細項
        self.object.items.all().delete()
        
        item_names = self.request.POST.getlist('item_names[]')
        item_amounts = self.request.POST.getlist('item_amounts[]')
        
        if item_names and item_amounts:
            for name, amount in zip(item_names, item_amounts):
                if name.strip() and amount:
                    ExpenseItem.objects.create(
                        expense=self.object,
                        name=name.strip(),
                        amount=amount
                    )

        # 刪除舊的分帳記錄
        self.object.splits.all().delete()

        # 處理分帳
        split_members = form.cleaned_data['split_members']
        split_equally = form.cleaned_data['split_equally']

        if split_equally and split_members:
            split_amount = self.object.amount / len(split_members)
            for member in split_members:
                ExpenseSplit.objects.create(
                    expense=self.object,
                    member=member,
                    amount=split_amount
                )

        messages.success(self.request, '記帳已更新！')
        return redirect('friend_expense:group_detail', pk=self.object.group.pk)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """刪除消費記錄"""
    model = Expense
    template_name = 'FriendExpense/expense_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, '記帳已刪除！')
        return reverse('friend_expense:group_detail', pk=self.object.group.pk)


class SettlementView(LoginRequiredMixin, DetailView):
    """結算頁面"""
    model = ExpenseGroup
    template_name = 'FriendExpense/settlement.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 計算每個成員的統計
        members_stats = []
        for member in self.object.members.all():
            members_stats.append({
                'member': member,
                'paid': member.get_total_paid(),
                'owed': member.get_total_owed(),
                'balance': member.get_balance()
            })
        context['members_stats'] = members_stats
        
        # 計算結算方案
        context['settlements'] = self.object.calculate_settlements()
        context['total_expense'] = self.object.get_total_expense()
        
        return context
