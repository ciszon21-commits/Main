from django.db import models


class FoundationExcavation(models.Model):
    project_code = models.CharField("計畫編號", max_length=100, default='Default Project', db_index=True)
    bridge_name = models.CharField("橋梁名稱", max_length=100, default='Default Bridge', db_index=True)
    bridge_id = models.CharField("基礎標識", max_length=50)
    column_base_el = models.FloatField("柱底EL (column_base_el)")
    h1_thickness = models.FloatField("版厚 (h1_thickness)")
    c_pc_thickness = models.FloatField("打底PC (c_pc_thickness)")

    # 幾何尺寸 (Geometry)
    B1 = models.FloatField("B1")
    B2 = models.FloatField("B2")
    L1 = models.FloatField("L1")
    L2 = models.FloatField("L2")

    # 地表高程 (Surface Elevations)
    el_l1_start = models.FloatField("L1起點地表EL")
    el_l1_end = models.FloatField("L1終點地表EL")
    el_l2_start = models.FloatField("L2起點地表EL")
    el_l2_end = models.FloatField("L2終點地表EL")
    el_b1_start = models.FloatField("B1起點地表EL")
    el_b1_end = models.FloatField("B1終點地表EL")
    el_b2_start = models.FloatField("B2起點地表EL")
    el_b2_end = models.FloatField("B2終點地表EL")

    # 間距參數 (Spacing parameters)
    offset_dist = models.FloatField("各階支撐退縮距離", default=0.8)
    d1_manual = models.FloatField("強制指定第一階支撐與地表之最小間距", default=0.5)

    excavation_plan = models.CharField("開挖平面", max_length=100, blank=True, null=True)
    excavation_section = models.CharField("開挖剖面", max_length=100, blank=True, null=True)
    skew_angle = models.FloatField("夾角", default=0.0)
    note = models.CharField("備註", max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    needs_review = models.BooleanField(default=False, verbose_name="資料更新需檢視")

    class Meta:
        verbose_name = "基礎開挖參數"
        verbose_name_plural = "基礎開挖參數"
        unique_together = ('project_code', 'bridge_name', 'bridge_id')
        ordering = ['project_code', 'bridge_name', 'bridge_id']

    def __str__(self):
        return f"{self.project_code} / {self.bridge_name} / {self.bridge_id}"
