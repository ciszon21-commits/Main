"""
GeoDataHub Models
==================
地圖導向資料管理平台的資料模型。

主要模型：
- GeoCategory: 資料分類
- GeoLocation: 地理位置（支援點、線、面）
- GeoDataSource: 資料來源（上傳、連結、OpenSearch）
- DataTag: 資料標籤
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import hashlib

User = get_user_model()


class DataTag(models.Model):
    """資料標籤模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='標籤名稱')
    slug = models.SlugField(max_length=50, unique=True, blank=True, verbose_name='URL 名稱')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        verbose_name = '資料標籤'
        verbose_name_plural = '資料標籤'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class GeoCategory(models.Model):
    """資料分類模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='分類名稱')
    icon = models.CharField(max_length=50, default='📍', verbose_name='圖示',
                           help_text='Emoji 或 CSS class 名稱')
    color = models.CharField(max_length=7, default='#0000FF', verbose_name='標記顏色',
                            help_text='Hex 色碼，例如 #FF0000')
    description = models.TextField(blank=True, verbose_name='說明')
    opensearch_pattern = models.CharField(max_length=100, blank=True, verbose_name='OpenSearch 索引模式',
                                         help_text='對應的 OpenSearch 索引模式，例如 sinoproject*')
    is_active = models.BooleanField(default=True, verbose_name='啟用')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '資料分類'
        verbose_name_plural = '資料分類'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class GeoLocation(models.Model):
    """地理位置模型 - 支援點、線、面"""
    
    class GeometryType(models.TextChoices):
        POINT = 'POINT', '點'
        LINE = 'LINE', '線'
        POLYGON = 'POLYGON', '面'
        MULTIPOINT = 'MULTIPOINT', '多點'

    # 主要座標 (用於點類型或作為代表點)
    latitude = models.DecimalField(
        max_digits=11, decimal_places=8,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name='緯度'
    )
    longitude = models.DecimalField(
        max_digits=12, decimal_places=8,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name='經度'
    )
    
    # 地址資訊
    address = models.CharField(max_length=500, blank=True, verbose_name='地址')
    city = models.CharField(max_length=100, blank=True, verbose_name='城市')
    district = models.CharField(max_length=100, blank=True, verbose_name='區域')
    country = models.CharField(max_length=100, default='台灣', verbose_name='國家')
    
    # 幾何資訊
    geometry_type = models.CharField(
        max_length=20,
        choices=GeometryType.choices,
        default=GeometryType.POINT,
        verbose_name='幾何類型'
    )
    geometry_data = models.JSONField(
        null=True, blank=True,
        verbose_name='幾何資料',
        help_text='GeoJSON 格式的座標資料'
    )
    
    # GeoHash (用於快速區域查詢)
    geo_hash = models.CharField(max_length=12, blank=True, db_index=True, verbose_name='GeoHash')
    
    # 精確度 (公尺)
    accuracy = models.FloatField(null=True, blank=True, verbose_name='精確度(公尺)')
    
    # 是否由使用者手動調整過
    is_manually_adjusted = models.BooleanField(default=False, verbose_name='已手動調整')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '地理位置'
        verbose_name_plural = '地理位置'
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['geo_hash']),
            models.Index(fields=['city']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        if self.address:
            return f"{self.address} ({self.latitude}, {self.longitude})"
        return f"({self.latitude}, {self.longitude})"

    def save(self, *args, **kwargs):
        # 自動計算 GeoHash
        if self.latitude and self.longitude and not self.geo_hash:
            self.geo_hash = self.calculate_geohash(float(self.latitude), float(self.longitude))
        super().save(*args, **kwargs)

    @staticmethod
    def calculate_geohash(lat: float, lon: float, precision: int = 8) -> str:
        """
        計算 GeoHash 編碼
        使用簡化版本：將座標轉為字串後 hash
        如需精確 GeoHash，可安裝 python-geohash 套件
        """
        # 簡化版 GeoHash：使用座標網格編碼
        # 每個精度級別減少約 5 倍誤差
        lat_normalized = (lat + 90) / 180  # 0-1
        lon_normalized = (lon + 180) / 360  # 0-1
        
        # 使用簡單的網格編碼
        grid_chars = '0123456789bcdefghjkmnpqrstuvwxyz'
        result = []
        
        lat_min, lat_max = 0.0, 1.0
        lon_min, lon_max = 0.0, 1.0
        
        for i in range(precision):
            if i % 2 == 0:  # 經度
                mid = (lon_min + lon_max) / 2
                if lon_normalized >= mid:
                    lon_min = mid
                    idx = 1
                else:
                    lon_max = mid
                    idx = 0
            else:  # 緯度
                mid = (lat_min + lat_max) / 2
                if lat_normalized >= mid:
                    lat_min = mid
                    idx = 1
                else:
                    lat_max = mid
                    idx = 0
            
            # 簡化：使用位置產生 hash 字符
            combined = int((lat_normalized * 1000 + lon_normalized * 1000 + i) % 32)
            result.append(grid_chars[combined])
        
        return ''.join(result)

    def to_geojson(self) -> dict:
        """將位置轉換為 GeoJSON 格式"""
        if self.geometry_type == self.GeometryType.POINT:
            return {
                "type": "Point",
                "coordinates": [float(self.longitude), float(self.latitude)]
            }
        elif self.geometry_data:
            return self.geometry_data
        return {
            "type": "Point",
            "coordinates": [float(self.longitude), float(self.latitude)]
        }


class GeoDataSource(models.Model):
    """資料來源模型 - 統一管理各類資料的地理資訊"""
    
    class SourceType(models.TextChoices):
        UPLOAD = 'upload', '使用者上傳'
        LINK = 'link', '外部連結'
        OPENSEARCH = 'opensearch', 'OpenSearch 資料'

    # 基本資訊
    title = models.CharField(max_length=300, verbose_name='標題')
    description = models.TextField(blank=True, verbose_name='描述')
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        verbose_name='來源類型'
    )
    
    # 分類與標籤
    category = models.ForeignKey(
        GeoCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_sources',
        verbose_name='分類'
    )
    tags = models.ManyToManyField(
        DataTag,
        blank=True,
        related_name='data_sources',
        verbose_name='標籤'
    )
    
    # 地理位置
    location = models.ForeignKey(
        GeoLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_sources',
        verbose_name='地理位置'
    )
    
    # 上傳檔案 (source_type = 'upload')
    file = models.FileField(
        upload_to='geodatahub/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='檔案'
    )
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='檔案大小(bytes)')
    file_type = models.CharField(max_length=100, blank=True, verbose_name='檔案類型')
    
    # 外部連結 (source_type = 'link')
    external_url = models.URLField(max_length=2000, blank=True, verbose_name='外部連結')
    
    # OpenSearch 參考 (source_type = 'opensearch')
    opensearch_index = models.CharField(max_length=200, blank=True, verbose_name='OpenSearch 索引')
    opensearch_doc_id = models.CharField(max_length=200, blank=True, verbose_name='OpenSearch 文件 ID')
    
    # 擴充欄位
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='中繼資料',
        help_text='額外的結構化資料'
    )
    
    # 縮圖
    thumbnail = models.ImageField(
        upload_to='geodatahub/thumbnails/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='縮圖'
    )
    
    # 狀態
    is_visible = models.BooleanField(default=True, verbose_name='公開顯示')
    is_featured = models.BooleanField(default=False, verbose_name='精選')
    view_count = models.PositiveIntegerField(default=0, verbose_name='瀏覽次數')
    
    # 審核與時間
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='geo_data_sources',
        verbose_name='建立者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '地理資料來源'
        verbose_name_plural = '地理資料來源'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['source_type']),
            models.Index(fields=['category']),
            models.Index(fields=['is_visible', '-created_at']),
            models.Index(fields=['opensearch_index', 'opensearch_doc_id']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 自動設定檔案資訊
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower() if '.' in self.file.name else ''
        super().save(*args, **kwargs)

    def increment_view_count(self):
        """增加瀏覽次數"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_opensearch_reference(self) -> dict:
        """取得 OpenSearch 參考資訊"""
        if self.source_type == self.SourceType.OPENSEARCH:
            return {
                'index': self.opensearch_index,
                'doc_id': self.opensearch_doc_id
            }
        return None


class GeoDataView(models.Model):
    """資料瀏覽記錄 - 用於分析"""
    source = models.ForeignKey(
        GeoDataSource,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='資料來源'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geo_data_views',
        verbose_name='使用者'
    )
    session_key = models.CharField(max_length=40, blank=True, verbose_name='Session Key')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP 位址')
    user_agent = models.CharField(max_length=500, blank=True, verbose_name='User Agent')
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='瀏覽時間')

    class Meta:
        verbose_name = '瀏覽記錄'
        verbose_name_plural = '瀏覽記錄'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['-viewed_at']),
            models.Index(fields=['source', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
        ]

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.source.title}"
