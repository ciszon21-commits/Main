from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models


def project_file_upload_to(instance: 'CompareProject', filename: str) -> str:
    extension = Path(filename).suffix.lower()
    return f'projects/{instance.pk}/{uuid4().hex}{extension}'


class CompareProject(models.Model):
    name = models.CharField(max_length=200)
    plan_number = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_compare_projects',
        db_index=True,
    )

    budget_xml = models.FileField(
        upload_to=project_file_upload_to,
        blank=True,
        null=True,
    )
    budget_original_name = models.CharField(max_length=255, blank=True)
    budget_records = models.JSONField(default=list, blank=True)
    budget_terms = models.JSONField(default=list, blank=True)

    quantity_sheet = models.FileField(
        upload_to=project_file_upload_to,
        blank=True,
        null=True,
    )
    quantity_original_name = models.CharField(max_length=255, blank=True)
    quantity_records = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Compare project'
        verbose_name_plural = 'Compare projects'

    def __str__(self) -> str:
        return f'{self.name} ({self.plan_number})'

    @property
    def has_budget(self) -> bool:
        return bool(self.budget_xml)

    @property
    def has_quantity_sheet(self) -> bool:
        return bool(self.quantity_sheet)

    @property
    def can_compare(self) -> bool:
        return self.has_budget and self.has_quantity_sheet


class ProjectAccess(models.Model):
    class Role(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        EDITOR = 'editor', 'Editor'
        MANAGER = 'manager', 'Manager'

    project = models.ForeignKey(
        CompareProject,
        on_delete=models.CASCADE,
        related_name='access_list',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='compare_project_access_list',
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.VIEWER,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project_id', 'role', 'user_id']
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'user'],
                name='compare_project_access_unique_project_user',
            )
        ]
        indexes = [
            models.Index(fields=['project', 'role']),
            models.Index(fields=['user', 'role']),
        ]

    def __str__(self) -> str:
        return f'ProjectAccess(project={self.project_id}, user={self.user_id}, role={self.role})'


class GlobalKeyword(models.Model):
    class Source(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        BUDGET = 'budget', 'Budget Upload'
        QUANTITY = 'quantity', 'Quantity Upload'
        MATCH = 'match', 'Match Feedback'

    term = models.CharField(max_length=120)
    normalized_term = models.CharField(max_length=120, unique=True, db_index=True)
    source = models.CharField(
        max_length=16,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    selected_count = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-selected_count', 'term']
        indexes = [
            models.Index(fields=['is_active', 'selected_count']),
        ]

    def __str__(self) -> str:
        return f'{self.term} ({self.normalized_term})'


class ComparisonRun(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    project = models.ForeignKey(
        CompareProject,
        on_delete=models.CASCADE,
        related_name='comparison_runs',
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    quantity_tolerance = models.DecimalField(max_digits=18, decimal_places=6)
    fuzzy_threshold = models.FloatField()
    weighted_threshold = models.FloatField()
    cross_encoder_threshold = models.FloatField(default=0.85)
    cross_encoder_total_threshold = models.FloatField(blank=True, null=True)
    sentence_model_name = models.CharField(
        max_length=200,
        default='paraphrase-multilingual-MiniLM-L12-v2',
    )
    cross_encoder_model_name = models.CharField(
        max_length=200,
        default='BAAI/bge-reranker-v2-m3',
    )
    baseline_meta = models.JSONField(default=dict, blank=True)
    report_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'created_at']),
            models.Index(fields=['project', 'status']),
        ]

    def __str__(self) -> str:
        return f'Run #{self.pk} - {self.project_id} - {self.status}'


class ComparisonMatch(models.Model):
    class Verdict(models.TextChoices):
        UNREVIEWED = 'unreviewed', 'Unreviewed'
        CORRECT = 'correct', 'Correct'
        INCORRECT = 'incorrect', 'Incorrect'

    run = models.ForeignKey(
        ComparisonRun,
        on_delete=models.CASCADE,
        related_name='matches',
    )
    method = models.CharField(max_length=64, db_index=True)
    rank = models.PositiveIntegerField(default=1)
    left_source_id = models.CharField(max_length=128, blank=True)
    right_source_id = models.CharField(max_length=128, blank=True)
    left_name = models.CharField(max_length=500, blank=True)
    right_name = models.CharField(max_length=500, blank=True)
    score = models.FloatField(default=0.0)
    name_score = models.FloatField(default=0.0)
    unit_score = models.FloatField(default=0.0)
    quantity_score = models.FloatField(default=0.0)
    verdict = models.CharField(
        max_length=16,
        choices=Verdict.choices,
        default=Verdict.UNREVIEWED,
        db_index=True,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['method', 'rank', 'id']
        indexes = [
            models.Index(fields=['run', 'method', 'rank']),
            models.Index(fields=['run', 'verdict']),
        ]

    def __str__(self) -> str:
        return f'Match #{self.pk} ({self.method})'
