from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="design_consistency_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self) -> str:
        return self.name


class ProjectFile(models.Model):
    FILE_TYPE_BUDGET = "budget_xml"
    FILE_TYPE_QUANTITY = "quantity_xls"
    FILE_TYPE_SPEC_PDF = "spec_pdf"
    FILE_TYPE_SPEC_DOC = "spec_doc"

    FILE_TYPE_CHOICES = [
        (FILE_TYPE_BUDGET, "Budget XML"),
        (FILE_TYPE_QUANTITY, "Quantity XLS/XLSX"),
        (FILE_TYPE_SPEC_PDF, "Spec PDF"),
        (FILE_TYPE_SPEC_DOC, "Spec DOC/DOCX"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="files",
    )
    file_type = models.CharField(max_length=32, choices=FILE_TYPE_CHOICES)
    file = models.FileField(upload_to="design_consistency/%Y/%m/%d/")
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="design_consistency_files",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.project.name} - {self.original_name}"


class ComparisonRun(models.Model):
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DONE, "Done"),
        (STATUS_FAILED, "Failed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="comparison_runs",
    )
    budget_file = models.ForeignKey(
        ProjectFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="budget_runs",
    )
    quantity_file = models.ForeignKey(
        ProjectFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quantity_runs",
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    result = models.JSONField(blank=True, null=True)
    report_file = models.FileField(
        upload_to="design_consistency/reports/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.project.name} run {self.created_at:%Y-%m-%d %H:%M}"


class ComparisonIssue(models.Model):
    TYPE_UNMATCHED_BUDGET = "unmatched_budget"
    TYPE_UNMATCHED_QUANTITY = "unmatched_quantity"
    TYPE_NAME_VARIANCE = "name_variance"
    TYPE_UNIT_MISMATCH = "unit_mismatch"
    TYPE_QTY_MISMATCH = "qty_mismatch"
    TYPE_LOW_CONFIDENCE = "low_confidence"

    ISSUE_TYPE_CHOICES = [
        (TYPE_UNMATCHED_BUDGET, "Budget only"),
        (TYPE_UNMATCHED_QUANTITY, "Quantity only"),
        (TYPE_NAME_VARIANCE, "名稱差異"),
        (TYPE_UNIT_MISMATCH, "Unit mismatch"),
        (TYPE_QTY_MISMATCH, "Quantity mismatch"),
        (TYPE_LOW_CONFIDENCE, "Low confidence match"),
    ]

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_FALSE_POSITIVE = "false_positive"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed mismatch"),
        (STATUS_FALSE_POSITIVE, "False positive"),
    ]

    run = models.ForeignKey(
        ComparisonRun,
        on_delete=models.CASCADE,
        related_name="issues",
    )
    issue_type = models.CharField(max_length=32, choices=ISSUE_TYPE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    summary = models.CharField(max_length=255)
    payload = models.JSONField(blank=True, null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.issue_type} ({self.status})"


class IntermediateItem(models.Model):
    """統一中介資料格式，將不同來源文件轉為同一結構以利比對。"""

    REFERENCE_BUDGET = "budget"
    REFERENCE_QUANTITY = "quantity"
    REFERENCE_SPEC = "spec"

    REFERENCE_CHOICES = [
        (REFERENCE_BUDGET, "預算書"),
        (REFERENCE_QUANTITY, "數量計算書"),
        (REFERENCE_SPEC, "規範附錄"),
    ]

    uid = models.CharField(
        max_length=128,
        unique=True,
        help_text="唯一識別碼，格式: {reference}_{file_id}_{row}",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="intermediate_items",
    )
    source_file = models.ForeignKey(
        ProjectFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intermediate_items",
    )
    item_name = models.CharField(
        max_length=500,
        help_text="原始名稱，保留原始文字",
    )
    standard_name = models.CharField(
        max_length=500,
        db_index=True,
        help_text="正規化名稱：去除空格、全半型轉換後的清潔名稱",
    )
    quantity = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="數量",
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="單位",
    )
    price = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="單價，供未來比對總價使用",
    )
    reference = models.CharField(
        max_length=32,
        choices=REFERENCE_CHOICES,
        help_text="來源標記：預算書 / 數量計算書 / 規範附錄",
    )
    item_no = models.CharField(
        max_length=100,
        blank=True,
        help_text="原始項次編號",
    )
    extra = models.JSONField(
        null=True,
        blank=True,
        help_text="擴充欄位（sheet 名稱、XML 路徑等）",
    )
    name_tokens = models.JSONField(
        null=True,
        blank=True,
        help_text="預計算的 token 清單，加速模糊比對",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["reference", "item_no", "created_at"]
        indexes = [
            models.Index(fields=["project", "reference"], name="idx_ii_proj_ref"),
            models.Index(fields=["project", "standard_name"], name="idx_ii_proj_stdname"),
        ]

    def __str__(self) -> str:
        return f"[{self.reference}] {self.item_name[:60]}"


class MatchResult(models.Model):
    """比對結果，記錄兩個 IntermediateItem 之間的匹配狀態。"""

    METHOD_EXACT = "exact"
    METHOD_FUZZY = "fuzzy"
    METHOD_TOKEN = "token"
    METHOD_ITEM_NO = "item_no"

    METHOD_CHOICES = [
        (METHOD_EXACT, "精準匹配"),
        (METHOD_FUZZY, "模糊匹配"),
        (METHOD_TOKEN, "Token 匹配"),
        (METHOD_ITEM_NO, "項次匹配"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="match_results",
    )
    run = models.ForeignKey(
        ComparisonRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="match_results",
    )
    item_a = models.ForeignKey(
        IntermediateItem,
        on_delete=models.CASCADE,
        related_name="matches_as_a",
        help_text="比對項 A",
    )
    item_b = models.ForeignKey(
        IntermediateItem,
        on_delete=models.CASCADE,
        related_name="matches_as_b",
        help_text="比對項 B",
    )
    match_method = models.CharField(
        max_length=32,
        choices=METHOD_CHOICES,
        help_text="匹配方式",
    )
    score = models.IntegerField(
        default=0,
        help_text="匹配分數 (0-100)",
    )
    is_name_consistent = models.BooleanField(
        default=False,
        help_text="名稱是否一致",
    )
    is_unit_consistent = models.BooleanField(
        default=False,
        help_text="單位是否一致",
    )
    is_qty_consistent = models.BooleanField(
        default=False,
        help_text="數量是否一致",
    )
    detail = models.JSONField(
        null=True,
        blank=True,
        help_text="差異細節（名稱 diff、數量差異等）",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "-created_at"]
        indexes = [
            models.Index(fields=["project", "match_method"], name="idx_mr_proj_method"),
        ]

    def __str__(self) -> str:
        return f"Match({self.match_method} {self.score}%): {self.item_a_id} ↔ {self.item_b_id}"

    @property
    def is_fully_consistent(self) -> bool:
        return self.is_name_consistent and self.is_unit_consistent and self.is_qty_consistent
