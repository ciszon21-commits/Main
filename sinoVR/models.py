from django.db import models

class Asset3D(models.Model):
    title = models.CharField(max_length=100, verbose_name="模型名稱")
    file = models.FileField(upload_to='sinoVR/assets/3d/', verbose_name="模型檔案 (.fbx)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "3D素材"
        verbose_name_plural = "3D素材"

class Panorama(models.Model):
    title = models.CharField(max_length=100, verbose_name="全景圖名稱")
    image = models.ImageField(upload_to='sinoVR/assets/360/', verbose_name="全景圖片")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "全景圖"
        verbose_name_plural = "全景圖"

class InfoCard(models.Model):
    title = models.CharField(max_length=200, verbose_name="字卡標題")
    content = models.TextField(verbose_name="字卡內容")
    bg_color = models.CharField(max_length=50, default='rgba(173, 216, 230, 0.95)', verbose_name="背景顏色")
    content_font_size = models.IntegerField(default=50, verbose_name="內容字體大小(px)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "資訊字卡"
        verbose_name_plural = "資訊字卡"

class Scene(models.Model):
    title = models.CharField(max_length=100, verbose_name="場景名稱")
    description = models.TextField(blank=True, verbose_name="場景描述")
    background = models.ForeignKey(Panorama, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="背景全景圖")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "VR場景"
        verbose_name_plural = "VR場景"

class SceneObject(models.Model):
    scene = models.ForeignKey(Scene, related_name='objects', on_delete=models.CASCADE, verbose_name="所屬場景")
    asset = models.ForeignKey(Asset3D, on_delete=models.CASCADE, null=True, blank=True, verbose_name="3D模型")
    info_card = models.ForeignKey(InfoCard, on_delete=models.CASCADE, null=True, blank=True, verbose_name="資訊字卡")
    
    # Transform
    position_x = models.FloatField(default=0, verbose_name="位置 X")
    position_y = models.FloatField(default=0, verbose_name="位置 Y")
    position_z = models.FloatField(default=0, verbose_name="位置 Z")
    
    rotation_x = models.FloatField(default=0, verbose_name="旋轉 X")
    rotation_y = models.FloatField(default=0, verbose_name="旋轉 Y")
    rotation_z = models.FloatField(default=0, verbose_name="旋轉 Z")
    
    scale_x = models.FloatField(default=1, verbose_name="縮放 X")
    scale_y = models.FloatField(default=1, verbose_name="縮放 Y")
    scale_z = models.FloatField(default=1, verbose_name="縮放 Z")

    def clean(self):
        from django.core.exceptions import ValidationError
        # 確保必須有 asset 或 info_card 其中之一
        if not self.asset and not self.info_card:
            raise ValidationError("場景物件必須關聯 3D 模型或資訊字卡")
        # 確保不能同時有兩者
        if self.asset and self.info_card:
            raise ValidationError("場景物件不能同時關聯 3D 模型和資訊字卡")

    def __str__(self):
        if self.asset:
            return f"{self.asset.title} in {self.scene.title}"
        elif self.info_card:
            return f"字卡: {self.info_card.title} in {self.scene.title}"
        return f"物件 in {self.scene.title}"

    class Meta:
        verbose_name = "場景物件"
        verbose_name_plural = "場景物件"
