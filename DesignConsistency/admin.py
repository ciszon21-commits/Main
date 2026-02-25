from django.contrib import admin

from .models import (
    ComparisonIssue,
    ComparisonRun,
    IntermediateItem,
    MatchResult,
    Project,
    ProjectFile,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "owner", "updated_at")
    search_fields = ("name", "code", "owner__username")
    list_filter = ("updated_at",)


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "file_type", "project", "uploaded_by", "uploaded_at")
    search_fields = ("original_name", "project__name", "uploaded_by__username")
    list_filter = ("file_type", "uploaded_at")


@admin.register(ComparisonRun)
class ComparisonRunAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "created_at", "report_file")
    list_filter = ("status", "created_at")


@admin.register(ComparisonIssue)
class ComparisonIssueAdmin(admin.ModelAdmin):
    list_display = ("run", "issue_type", "status", "summary", "created_at")
    list_filter = ("issue_type", "status")
    search_fields = ("summary",)


@admin.register(IntermediateItem)
class IntermediateItemAdmin(admin.ModelAdmin):
    list_display = ("uid", "item_name_short", "reference", "quantity", "unit", "price", "project")
    list_filter = ("reference", "project")
    search_fields = ("uid", "item_name", "standard_name", "item_no")
    readonly_fields = ("uid", "standard_name", "name_tokens", "created_at")

    @admin.display(description="名稱")
    def item_name_short(self, obj):
        return obj.item_name[:80] if obj.item_name else ""


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = (
        "item_a",
        "item_b",
        "match_method",
        "score",
        "is_name_consistent",
        "is_unit_consistent",
        "is_qty_consistent",
        "created_at",
    )
    list_filter = ("match_method", "is_name_consistent", "is_unit_consistent", "is_qty_consistent")
    search_fields = ("item_a__item_name", "item_b__item_name")
