from django.db import models
from django.contrib.auth.models import User

# ==============================================================================
# 基礎資料模型 (Base Data Models)
# ------------------------------------------------------------------------------
# 這些模型儲存系統的靜態參考資料，由 Excel 匯入，通常不隨使用者操作變動。
# ==============================================================================

class MainCategory(models.Model):
    """
    14個主要工程大項分類 (如: 結構工程、裝修工程...)
    對應 Excel 中的各大類別。
    """
    code = models.CharField(max_length=10, unique=True, verbose_name="分類代碼")
    name = models.CharField(max_length=100, verbose_name="分類名稱")
    order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        verbose_name = "主要分類"
        verbose_name_plural = "主要分類"
        ordering = ['order', 'code']

    def __str__(self):
        return f"{self.code} {self.name}"


class ComponentItem(models.Model):
    """
    組件項目資料 (Component Items)
    包含所有細項的詳細資訊、碳排係數與造價資訊。
    """
    # 關聯設定
    category = models.ForeignKey(
        MainCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="所屬分類"
    )
    
    # 項目基本資訊
    item_no = models.CharField(max_length=20, unique=True, verbose_name="項次")
    level = models.IntegerField(
        default=3,
        verbose_name="階層",
        help_text="1=工程大項(如'一'), 2=中項(如'一.1'), 3=細項(如'一.1.1')"
    )
    work_item = models.CharField(max_length=200, verbose_name="工作項目")
    unit = models.CharField(max_length=20, blank=True, verbose_name="單位")
    description = models.CharField(max_length=500, blank=True, verbose_name="說明") # Increased length for flexibility
    
    # 預設值
    default_quantity = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name="預設數量"
    )
    
    # 碳排係數 (Carbon Factors)
    carbon_before = models.DecimalField(
        max_digits=15, decimal_places=6,
        null=True, blank=True,
        verbose_name="減碳前單位碳排量 (kgCO2e/單位)"
    )
    carbon_after = models.DecimalField(
        max_digits=15, decimal_places=6,
        null=True, blank=True,
        verbose_name="減碳後單位碳排量 (kgCO2e/單位)"
    )
    carbon_unit = models.CharField(max_length=50, blank=True, verbose_name="碳排單位")
    
    # 造價資訊 (Cost Factors)
    cost_before = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name="減碳前單位造價費用 (元/單位)"
    )
    cost_after = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name="減碳後單位造價費用 (元/單位)"
    )
    
    # 其他資訊
    notes = models.TextField(blank=True, verbose_name="備註")
    reference = models.TextField(blank=True, verbose_name="說明(出處/連結)")
    order = models.IntegerField(default=0, verbose_name="排序")
    
    class Meta:
        verbose_name = "組件項目"
        verbose_name_plural = "組件項目"
        ordering = ['category__order', 'category__code', 'order', 'item_no']
    
    def __str__(self):
        return f"{self.item_no} {self.work_item}"


# ==============================================================================
# 方案管理模型 (Scenario Management Models)
# ------------------------------------------------------------------------------
# 這些模型儲存使用者建立的專案與方案數據，支援多人協作與資料儲存。
# ==============================================================================

class Scenario(models.Model):
    """
    方案 (Scenario)
    代表一個獨立的碳排計算專案，包含計畫資訊與權限設定。
    """
    # 專案基本資訊
    project_number = models.CharField(max_length=50, verbose_name="計畫編號")
    project_name = models.CharField(max_length=200, verbose_name="計畫名稱")
    scenario_name = models.CharField(max_length=200, verbose_name="方案名稱")
    description = models.TextField(blank=True, verbose_name="方案說明")
    
    # 權限與人員 (Permissions)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_scenarios',
        verbose_name="建立者",
        null=True,  # 允許未登入使用者創建 (訪客模式)
        blank=True
    )
    collaborators = models.ManyToManyField(
        User,
        related_name='collaborative_scenarios',
        blank=True,
        verbose_name="共同編輯人"
    )
    
    # 時間戳記 (Timestamps)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更新時間")
    
    class Meta:
        verbose_name = "方案"
        verbose_name_plural = "方案"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['project_number']),
            models.Index(fields=['creator']),
        ]
    
    def __str__(self):
        return f"{self.project_number} - {self.scenario_name}"
    
    def can_edit(self, user):
        """檢查用戶是否可編輯此方案"""
        if not self.creator: # 訪客創建的，理論上誰都能改，或只有當下 session 能改 (這裡簡化處裡)
            return True 
        return self.creator == user or user in self.collaborators.all()
    
    def can_delete(self, user):
        """檢查用戶是否可刪除此方案（僅創建者可刪除，若無創建者則視為公開/訪客方案允許刪除）"""
        if not self.creator: 
            return True
        return self.creator == user


class ScenarioData(models.Model):
    """
    方案數據 (Scenario Data)
    記錄特定方案中，各個組件項目的輸入數量。
    此表為 Scenario 與 ComponentItem 的中間表，並附加 quantity。
    """
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        related_name='data',
        verbose_name="所屬方案"
    )
    category = models.ForeignKey(
        MainCategory,
        on_delete=models.CASCADE,
        verbose_name="所屬分類"
    )
    component_item = models.ForeignKey(
        ComponentItem,
        on_delete=models.CASCADE,
        verbose_name="組件項目"
    )
    
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="數量"
    )
    
    last_saved_at = models.DateTimeField(auto_now=True, verbose_name="最後儲存時間")
    
    class Meta:
        verbose_name = "方案數據"
        verbose_name_plural = "方案數據"
        unique_together = ['scenario', 'component_item'] # 確保每個方案中，每個組件只有一筆資料
        indexes = [
            models.Index(fields=['scenario', 'category']),
        ]
    
    def __str__(self):
        return f"{self.scenario.scenario_name} - {self.component_item.item_no}"
