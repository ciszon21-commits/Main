from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class ExpenseGroup(models.Model):
    """記帳群組"""
    name = models.CharField(max_length=100, verbose_name="群組名稱")
    description = models.TextField(blank=True, verbose_name="群組說明")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expense_groups',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "記帳群組"
        verbose_name_plural = "記帳群組"
        ordering = ['-created_at']

    def get_total_expense(self):
        """取得群組總支出"""
        return self.expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

    def calculate_settlements(self):
        """計算結算"""
        members = list(self.members.all())
        if not members:
            return []

        # 計算每個成員的淨額（支出 - 應付）
        balances = {}
        for member in members:
            # 成員支付的總額
            paid = self.expenses.filter(paid_by=member).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            # 成員應付的總額
            owed = ExpenseSplit.objects.filter(
                expense__group=self,
                member=member
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            balances[member] = paid - owed

        # 分離債權人（正淨額）和債務人（負淨額）
        creditors = [(m, b) for m, b in balances.items() if b > 0]
        debtors = [(m, -b) for m, b in balances.items() if b < 0]
        
        # 排序以優化配對
        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)
        
        # 計算最小轉帳
        settlements = []
        i, j = 0, 0
        
        while i < len(creditors) and j < len(debtors):
            creditor, credit = creditors[i]
            debtor, debt = debtors[j]
            
            amount = min(credit, debt)
            if amount > Decimal('0.01'):  # 忽略極小金額
                settlements.append({
                    'from_member': debtor,
                    'to_member': creditor,
                    'amount': amount
                })
            
            credit -= amount
            debt -= amount
            creditors[i] = (creditor, credit)
            debtors[j] = (debtor, debt)
            
            if credit <= Decimal('0.01'):
                i += 1
            if debt <= Decimal('0.01'):
                j += 1
        
        return settlements


class Member(models.Model):
    """群組成員"""
    group = models.ForeignKey(
        ExpenseGroup,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="所屬群組"
    )
    name = models.CharField(max_length=100, verbose_name="成員名稱")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expense_memberships',
        verbose_name="關聯使用者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="加入時間")

    def __str__(self):
        return f"{self.name} ({self.group.name})"

    class Meta:
        verbose_name = "群組成員"
        verbose_name_plural = "群組成員"
        unique_together = ['group', 'name']

    def get_total_paid(self):
        """取得成員支付總額"""
        return self.paid_expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

    def get_total_owed(self):
        """取得成員應付總額"""
        return self.expense_splits.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

    def get_balance(self):
        """取得成員淨額（正數表示應收）"""
        return self.get_total_paid() - self.get_total_owed()


class ExpenseCategory(models.Model):
    """消費分類"""
    group = models.ForeignKey(
        ExpenseGroup,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="所屬群組"
    )
    name = models.CharField(max_length=50, verbose_name="分類名稱")
    
    class Meta:
        verbose_name = "消費分類"
        verbose_name_plural = "消費分類"
        unique_together = ['group', 'name']

    def __str__(self):
        return self.name


class Expense(models.Model):
    """消費記錄"""
    group = models.ForeignKey(
        ExpenseGroup,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name="所屬群組"
    )
    paid_by = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='paid_expenses',
        verbose_name="付款人"
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name="分類"
    )
    description = models.CharField(max_length=200, verbose_name="品項說明")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="金額"
    )
    receipt = models.ImageField(upload_to='expenses/%Y/%m/', blank=True, null=True, verbose_name='收據/照片')
    expense_date = models.DateTimeField(default=timezone.now, verbose_name="消費時間")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    notes = models.TextField(blank=True, verbose_name="備註")

    def __str__(self):
        return f"{self.description} - ${self.amount}"

    class Meta:
        verbose_name = "消費記錄"
        verbose_name_plural = "消費記錄"
        ordering = ['-expense_date']


class ExpenseSplit(models.Model):
    """分帳記錄"""
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='splits',
        verbose_name="關聯消費"
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='expense_splits',
        verbose_name="分攤成員"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="分攤金額"
    )

    def __str__(self):
        return f"{self.member.name} 分攤 ${self.amount}"

    class Meta:
        verbose_name = "分帳記錄"
        verbose_name_plural = "分帳記錄"
        unique_together = ['expense', 'member']


class ExpenseItem(models.Model):
    """消費細項"""
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="關聯消費"
    )
    name = models.CharField(max_length=100, verbose_name="品項名稱")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="金額"
    )

    def __str__(self):
        return f"{self.name} - ${self.amount}"

    class Meta:
        verbose_name = "消費細項"
        verbose_name_plural = "消費細項"
