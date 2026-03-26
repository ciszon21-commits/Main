from django.db import models
import uuid
from django.conf import settings

class Project(models.Model):
    """
    專案基本資訊：存儲專案名稱、地理位置中心點等。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="專案名稱")
    location = models.CharField(max_length=255, blank=True, verbose_name="地址/地點描述")
    center_lat = models.FloatField(verbose_name="中心緯度")
    center_lng = models.FloatField(verbose_name="中心經度")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lumasite_projects', verbose_name="擁有者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "專案"
        verbose_name_plural = "專案"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Scenario(models.Model):
    """
    方案模型：一個專案下可有多個方案 (如 A 方案、B 方案)。
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scenarios', verbose_name="關聯專案")
    name = models.CharField(max_length=255, verbose_name="方案名稱")
    description = models.TextField(blank=True, verbose_name="方案描述")
    is_active = models.BooleanField(default=False, verbose_name="是否為當前方案")
    version_no = models.IntegerField(default=1, verbose_name="版本號")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "分析方案"
        verbose_name_plural = "分析方案"

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class SceneAsset(models.Model):
    """
    場景資產：存儲 3D 模型、地形、Context 等資源路徑。
    """
    ASSET_TYPES = (
        ('terrain', '地形'),
        ('context', '周邊建物'),
        ('design', '設計量體'),
        ('tree', '植栽'),
    )
    SOURCE_TYPES = (
        ('osm', 'OpenStreetMap'),
        ('upload', '使用者上傳'),
        ('generated', '系統生成'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='assets', verbose_name="關聯方案")
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, verbose_name="資產類型")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, verbose_name="來源類型")
    file = models.FileField(upload_to='lumasite/assets/%Y/%m/%d/', verbose_name="資產檔案")
    transform_json = models.JSONField(default=dict, blank=True, verbose_name="轉換矩陣 (JSON)")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="元數據 (JSON)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "場景資產"
        verbose_name_plural = "場景資產"

class AnalysisRun(models.Model):
    """
    分析紀錄：記錄每一筆分析任務的狀態與參數。
    """
    ANALYSIS_TYPES = (
        ('instant', '單一時刻陰影'),
        ('hours', '曝曬時數'),
        ('solar', '日射量分析'),
    )
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '執行中'),
        ('success', '成功'),
        ('failed', '失敗'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='analysis_runs', verbose_name="關聯方案")
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES, verbose_name="分析類型")
    parameters = models.JSONField(default=dict, verbose_name="分析參數 (JSON)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="執行狀態")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="開始時間")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="結束時間")
    error_message = models.TextField(blank=True, verbose_name="錯誤訊息")

    class Meta:
        verbose_name = "分析任務"
        verbose_name_plural = "分析任務"

class AnalysisResult(models.Model):
    """
    分析結果：存儲分析後產生的結果檔 (如 Heatmap, Mesh, CSV)。
    """
    RESULT_TYPES = (
        ('raster', '柵格 (Heatmap)'),
        ('mesh', '網格 (Mesh)'),
        ('csv', '數據報表'),
        ('image', '截圖/影像'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis_run = models.OneToOneField(AnalysisRun, on_delete=models.CASCADE, related_name='result', verbose_name="關聯任務")
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES, verbose_name="結果類型")
    data_file = models.FileField(upload_to='lumasite/results/%Y/%m/%d/', verbose_name="結果檔案")
    summary = models.JSONField(default=dict, blank=True, verbose_name="統計摘要 (JSON)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "分析結果"
        verbose_name_plural = "分析結果"
