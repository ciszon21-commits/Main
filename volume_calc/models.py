from django.db import models

class ProjectCase(models.Model):
    name = models.CharField(max_length=255, default='New Case', verbose_name="案件編號")
    base_area = models.FloatField(verbose_name="基地面積")
    original_volume = models.FloatField(verbose_name="建物原容積")
    zone_type = models.CharField(max_length=50, verbose_name="使用分區")
    volume_ratio = models.FloatField(verbose_name="容積率")
    
    # Store settings for rules (e.g. which rules apply, percentage input)
    reward_parameters = models.JSONField(default=dict, blank=True, verbose_name="獎勵參數設定")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.zone_type}"

    class Meta:
        verbose_name = '專案容積計算'
        verbose_name_plural = '專案容積計算'
