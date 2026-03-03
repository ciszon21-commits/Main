from django.db import models
from django.contrib.auth.models import User


class Restaurant(models.Model):
    """便當店模型"""
    
    name = models.CharField(
        max_length=100,
        verbose_name="店名"
    )
    phone = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="電話"
    )
    image_file = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="菜單圖片檔名",
        help_text="例如: menu_dianguo.jpg, 檔案需放在 static/LunchOrder/ 下"
    )
    address = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="地址"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="營業中"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "便當店"
        verbose_name_plural = "便當店"
        ordering = ['name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """菜單項目模型"""
    
    CATEGORY_CHOICES = [
        ('chicken', '雞肉餐盒'),
        ('duck', '鴨肉料理'),
        ('pork', '豬肉餐盒'),
        ('beef', '牛肉餐盒'),
        ('fish', '鮮魚餐盒'),
        ('noodle', '麵食/粥品'),
        ('soup', '精選湯品'),
        ('veg', '蔬食餐盒'),
        ('side', '美味小菜'),
        ('single', '單點品項'),
        ('drink', '冷泡茶飲'),
        ('other', '其他'),
    ]
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name="便當店"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="品項名稱"
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=0,
        verbose_name="價格"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='single',
        verbose_name="分類"
    )
    description = models.TextField(
        blank=True,
        verbose_name="說明"
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name="供應中"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "菜單項目"
        verbose_name_plural = "菜單項目"
        ordering = ['restaurant', 'name']

    def __str__(self):
        return f"{self.restaurant.name} - {self.name} (${self.price})"


class LunchOrder(models.Model):
    """訂單模型"""
    
    employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='lunch_orders',
        verbose_name="員工",
        null=True,
        blank=True
    )
    employee_name = models.CharField(
        max_length=100,
        verbose_name="員工全名",
        help_text="訂購時的員工姓名"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="訂購品項"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="數量"
    )
    order_date = models.DateField(
        verbose_name="訂購日期"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="備註"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "訂單"
        verbose_name_plural = "訂單"
        ordering = ['-order_date', '-created_at']

    def __str__(self):
        return f"{self.employee_name} - {self.menu_item.name} x {self.quantity}"

    @property
    def subtotal(self):
        """計算小計"""
        return self.menu_item.price * self.quantity

    def save(self, *args, **kwargs):
        # 自動填入員工全名
        if not self.employee_name and self.employee:
            full_name = self.employee.get_full_name()
            self.employee_name = full_name if full_name else self.employee.username
        super().save(*args, **kwargs)


class RestaurantSchedule(models.Model):
    """每日便當店排程"""
    
    date = models.DateField(
        unique=True,
        verbose_name="日期"
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="便當店"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "便當店排程"
        verbose_name_plural = "便當店排程"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.restaurant.name}"
