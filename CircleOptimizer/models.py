from django.db import models
from django.core.validators import MinValueValidator
import json


class Shape(models.Model):
    """凸字形圖形模型，儲存8個控制點"""
    name = models.CharField(max_length=200, verbose_name="名稱")
    points = models.JSONField(
        verbose_name="控制點座標",
        help_text="JSON陣列，包含8個點的座標，格式: [[x1,y1], [x2,y2], ...]"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "隧道斷面圖形"
        verbose_name_plural = "隧道斷面圖形"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def points_count(self):
        """返回控制點數量"""
        if isinstance(self.points, str):
            points = json.loads(self.points)
        else:
            points = self.points
        return len(points) if points else 0


class CircleConfig(models.Model):
    """圓配置模型，儲存3心圓或4心圓的配置資訊"""
    CONFIG_TYPE_CHOICES = [
        ('3_circle', '3心圓'),
        ('4_circle', '4心圓'),
    ]

    shape = models.ForeignKey(
        Shape,
        on_delete=models.CASCADE,
        related_name='configs',
        verbose_name="圖形"
    )
    config_type = models.CharField(
        max_length=20,
        choices=CONFIG_TYPE_CHOICES,
        verbose_name="配置類型"
    )
    total_area = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name="總面積"
    )
    is_optimized = models.BooleanField(
        default=True,
        verbose_name="是否為優化結果"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "隧道斷面配置"
        verbose_name_plural = "隧道斷面配置"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shape.name} - {self.get_config_type_display()}"

    @property
    def circle_count(self):
        """返回圓的數量"""
        return self.circles.count()


class Circle(models.Model):
    """單個圓的參數模型"""
    config = models.ForeignKey(
        CircleConfig,
        on_delete=models.CASCADE,
        related_name='circles',
        verbose_name="圓配置"
    )
    circle_index = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="圓索引"
    )
    center_x = models.FloatField(verbose_name="圓心X座標")
    center_y = models.FloatField(verbose_name="圓心Y座標")
    radius = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name="半徑"
    )
    arc_length = models.FloatField(
        validators=[MinValueValidator(0)],
        verbose_name="弧長"
    )
    start_angle = models.FloatField(
        verbose_name="起始角度（度）",
        help_text="以度為單位，0-360"
    )
    end_angle = models.FloatField(
        verbose_name="結束角度（度）",
        help_text="以度為單位，0-360"
    )

    class Meta:
        verbose_name = "圓"
        verbose_name_plural = "圓"
        ordering = ['circle_index']
        unique_together = ['config', 'circle_index']

    def __str__(self):
        return f"圓 {self.circle_index} (中心: {self.center_x:.2f}, {self.center_y:.2f}, 半徑: {self.radius:.2f})"
