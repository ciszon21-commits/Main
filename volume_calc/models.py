from django.db import models

class VolumeCalculation(models.Model):
    """
    容積獎勵及建築量體計算模型
    """
    project_name = models.CharField(max_length=255, verbose_name="專案名稱", blank=True)
    base_area = models.FloatField(verbose_name="基地面積 (㎡)", default=0.0)
    original_volume = models.FloatField(verbose_name="建物原容積 (㎡)", default=0.0)
    land_use_zone = models.CharField(max_length=100, verbose_name="使用分區", blank=True)
    floor_area_ratio = models.FloatField(verbose_name="容積率 (%)", default=0.0)
    
    # 儲存獎勵項目的 JSON 資料，例如：[{"name": "都市更新", "type": "percentage", "value": 10}, ...]
    reward_items = models.JSONField(verbose_name="獎勵項目明細", default=list, blank=True)
    
    # 計算後的摘要欄位
    total_reward_volume = models.FloatField(verbose_name="總獎勵容積", default=0.0)
    final_volume = models.FloatField(verbose_name="總容積 (含獎勵)", default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "容積計算紀錄"
        verbose_name = "容積計算紀錄列表"

    def __str__(self):
        return f"{self.project_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
