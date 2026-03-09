from django.db import models
from django.conf import settings


class Project(models.Model):
    """專案 — 對應一本 PDF 報告書"""
    name = models.CharField("專案名稱", max_length=255)
    description = models.TextField("專案說明", blank=True, default="")
    pdf_file = models.FileField("PDF 報告書", upload_to="review_feedback/pdfs/", blank=True, null=True)
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="admin_projects",
        verbose_name="專案管理員",
    )
    experts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="expert_projects",
        verbose_name="專家審查員",
    )
    created_at = models.DateTimeField("建立時間", auto_now_add=True)
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        verbose_name = "專案"
        verbose_name_plural = "專案"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def total_entries(self):
        return ComparisonEntry.objects.filter(comparison_file__project=self).count()

    @property
    def reviewed_entries(self):
        return ComparisonEntry.objects.filter(
            comparison_file__project=self,
            review_feedbacks__isnull=False
        ).distinct().count()


class ComparisonFile(models.Model):
    """上傳的 JSON 比對結果檔案"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="comparison_files",
        verbose_name="所屬專案",
    )
    file = models.FileField("JSON 檔案", upload_to="review_feedback/json/")
    original_filename = models.CharField("原始檔名", max_length=512)
    uploaded_at = models.DateTimeField("上傳時間", auto_now_add=True)

    class Meta:
        verbose_name = "比對結果檔"
        verbose_name_plural = "比對結果檔"
        ordering = ["original_filename"]

    def __str__(self):
        return self.original_filename

    @property
    def entry_count(self):
        return self.entries.count()

    @property
    def reviewed_count(self):
        return self.entries.filter(review_feedbacks__isnull=False).distinct().count()


class ComparisonEntry(models.Model):
    """單筆比對結果"""
    comparison_file = models.ForeignKey(
        ComparisonFile,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name="所屬比對檔",
    )
    strategy_name = models.TextField("減碳策略名稱")
    excerpt_text = models.TextField("文字摘錄")
    source_page = models.CharField("來源頁碼", max_length=20, blank=True, default="")
    reasoning = models.TextField("AI 推論說明", blank=True, default="")
    is_match = models.BooleanField("是否匹配", default=False)
    arbitration_status = models.CharField("仲裁狀態", max_length=50, blank=True, default="")
    arbitration_note = models.JSONField("仲裁備註", blank=True, null=True)
    final_decision_class = models.CharField("最終判定分類", max_length=255, blank=True, default="")

    # char_interval for reference
    char_start_pos = models.IntegerField("字元起始位置", blank=True, null=True)
    char_end_pos = models.IntegerField("字元結束位置", blank=True, null=True)

    class Meta:
        verbose_name = "比對結果"
        verbose_name_plural = "比對結果"
        ordering = ["source_page", "char_start_pos"]

    def __str__(self):
        return f"[P.{self.source_page}] {self.excerpt_text[:40]}..."

    @property
    def latest_feedback(self):
        return self.review_feedbacks.order_by("-reviewed_at").first()


class ReviewFeedback(models.Model):
    """使用者審查回饋"""
    IS_CORRECT_CHOICES = [
        (None, "尚未審查"),
        (True, "正確"),
        (False, "不正確"),
    ]

    entry = models.ForeignKey(
        ComparisonEntry,
        on_delete=models.CASCADE,
        related_name="review_feedbacks",
        verbose_name="比對結果",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_feedbacks",
        verbose_name="審查者",
    )
    is_correct = models.BooleanField("判定是否正確", null=True, blank=True)
    correct_classification = models.CharField("正確分類", max_length=255, blank=True, default="")
    feedback_reason = models.TextField("備註說明", blank=True, default="")
    additional_description = models.TextField("手段描述擴充", blank=True, default="")
    reviewed_at = models.DateTimeField("審查時間", auto_now_add=True)
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        verbose_name = "審查回饋"
        verbose_name_plural = "審查回饋"
        ordering = ["-reviewed_at"]

    def __str__(self):
        status = "✓" if self.is_correct else ("✗" if self.is_correct is False else "?")
        return f"[{status}] {self.entry}"
