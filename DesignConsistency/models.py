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
