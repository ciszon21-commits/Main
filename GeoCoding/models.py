from django.db import models


class County(models.Model):
    """縣市資料"""
    name = models.CharField(max_length=50, unique=True, verbose_name="縣市名稱")
    latitude = models.FloatField(verbose_name="中心點緯度")
    longitude = models.FloatField(verbose_name="中心點經度")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "縣市"
        verbose_name_plural = "縣市"
        ordering = ['name']


class Township(models.Model):
    """鄉鎮區資料"""
    county = models.ForeignKey(
        County, 
        on_delete=models.CASCADE, 
        related_name="townships",
        verbose_name="所屬縣市"
    )
    name = models.CharField(max_length=50, verbose_name="鄉鎮區名稱")
    latitude = models.FloatField(verbose_name="中心點緯度")
    longitude = models.FloatField(verbose_name="中心點經度")

    def __str__(self):
        return f"{self.county.name}{self.name}"

    class Meta:
        verbose_name = "鄉鎮區"
        verbose_name_plural = "鄉鎮區"
        unique_together = ['county', 'name']
        ordering = ['county', 'name']


class Village(models.Model):
    """村里資料"""
    township = models.ForeignKey(
        Township,
        on_delete=models.CASCADE,
        related_name="villages",
        verbose_name="所屬鄉鎮區"
    )
    name = models.CharField(max_length=50, verbose_name="村里名稱")
    latitude = models.FloatField(verbose_name="中心點緯度")
    longitude = models.FloatField(verbose_name="中心點經度")

    def __str__(self):
        return f"{self.township}{self.name}"

    class Meta:
        verbose_name = "村里"
        verbose_name_plural = "村里"
        unique_together = ['township', 'name']
        ordering = ['township', 'name']


class Landmark(models.Model):
    """地標/景點資料 (POI)"""
    CATEGORY_CHOICES = [
        ('mountain', '山岳'),
        ('lake', '湖泊'),
        ('park', '公園'),
        ('scenic', '風景區'),
        ('temple', '寺廟'),
        ('station', '車站'),
        ('airport', '機場'),
        ('port', '港口'),
        ('university', '大學'),
        ('hospital', '醫院'),
        ('museum', '博物館'),
        ('shopping', '商圈'),
        ('night_market', '夜市'),
        ('beach', '海灘'),
        ('hot_spring', '溫泉'),
        ('other', '其他'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="地標名稱")
    aliases = models.CharField(max_length=500, blank=True, verbose_name="別名（逗號分隔）")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name="類別")
    county = models.ForeignKey(
        County,
        on_delete=models.CASCADE,
        related_name="landmarks",
        verbose_name="所屬縣市"
    )
    township = models.ForeignKey(
        Township,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="landmarks",
        verbose_name="所屬鄉鎮區"
    )
    latitude = models.FloatField(verbose_name="緯度")
    longitude = models.FloatField(verbose_name="經度")
    description = models.TextField(blank=True, verbose_name="說明")

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def get_aliases_list(self):
        """取得別名列表"""
        if self.aliases:
            return [a.strip() for a in self.aliases.split(',')]
        return []

    class Meta:
        verbose_name = "地標"
        verbose_name_plural = "地標"
        ordering = ['county', 'category', 'name']


class GeoQuery(models.Model):
    """地理編碼查詢紀錄"""
    query_text = models.CharField(max_length=500, verbose_name="查詢字串")
    matched_county = models.ForeignKey(
        County,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queries",
        verbose_name="匹配縣市"
    )
    matched_township = models.ForeignKey(
        Township,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queries",
        verbose_name="匹配鄉鎮區"
    )
    matched_village = models.ForeignKey(
        Village,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queries",
        verbose_name="匹配村里"
    )
    latitude = models.FloatField(null=True, blank=True, verbose_name="回傳緯度")
    longitude = models.FloatField(null=True, blank=True, verbose_name="回傳經度")
    confidence = models.FloatField(default=0.0, verbose_name="匹配信心度")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="查詢時間")

    def __str__(self):
        parts = []
        if self.matched_county:
            parts.append(self.matched_county.name)
        if self.matched_township:
            parts.append(self.matched_township.name)
        if self.matched_village:
            parts.append(self.matched_village.name)
        result = ''.join(parts) or '未知'
        return f"{self.query_text} → {result}"

    class Meta:
        verbose_name = "查詢紀錄"
        verbose_name_plural = "查詢紀錄"
        ordering = ['-created_at']

