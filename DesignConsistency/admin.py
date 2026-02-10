from django.contrib import admin

from .models import ComparisonIssue, ComparisonRun, Project, ProjectFile


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
