from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class ExpenseCategory(models.Model):
    """支出類型"""
    name = models.CharField(max_length=50, verbose_name="類型名稱")
    icon = models.CharField(max_length=50, blank=True, default="bi-tag", verbose_name="圖示")
    color = models.CharField(max_length=20, blank=True, default="#6c757d", verbose_name="顏色")
    is_default = models.BooleanField(default=False, verbose_name="預設類型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "支出類型"
        verbose_name_plural = "支出類型"
        ordering = ['name']


class Participant(models.Model):
    """分帳參與者"""
    name = models.CharField(max_length=100, verbose_name="參與者名稱")
    email = models.EmailField(blank=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="啟用中")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "參與者"
        verbose_name_plural = "參與者"
        ordering = ['name']


class Expense(models.Model):
    """記帳紀錄"""
    date = models.DateField(default=timezone.now, verbose_name="日期", db_index=True)
    time = models.TimeField(default=timezone.now, verbose_name="時間")
    item_name = models.CharField(max_length=200, verbose_name="品項名稱")
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='expenses',
        verbose_name="類型"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="金額"
    )
    note = models.TextField(blank=True, verbose_name="備註")
    paid_by = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_expenses',
        verbose_name="付款人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return f"{self.date} - {self.item_name} ({self.amount})"

    class Meta:
        verbose_name = "記帳紀錄"
        verbose_name_plural = "記帳紀錄"
        ordering = ['-date', '-time']


class ExpenseSplit(models.Model):
    """費用分攤"""
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='splits',
        verbose_name="關聯記帳"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='expense_splits',
        verbose_name="分攤者"
    )
    share_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="應分攤金額"
    )

    def __str__(self):
        return f"{self.participant.name} - {self.share_amount}"

    class Meta:
        verbose_name = "費用分攤"
        verbose_name_plural = "費用分攤"
        unique_together = ['expense', 'participant']
