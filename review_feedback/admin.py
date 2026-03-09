from django.contrib import admin
from .models import Project, ComparisonFile, ComparisonEntry, ReviewFeedback
from .services import parse_comparison_json


class ComparisonFileInline(admin.TabularInline):
    model = ComparisonFile
    extra = 1
    readonly_fields = ("original_filename", "uploaded_at")
    fields = ("file", "original_filename", "uploaded_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "total_entries", "reviewed_entries", "created_at")
    search_fields = ("name", "description")
    inlines = [ComparisonFileInline]


@admin.register(ComparisonFile)
class ComparisonFileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "project", "entry_count", "reviewed_count", "uploaded_at")
    list_filter = ("project",)
    search_fields = ("original_filename",)
    readonly_fields = ("original_filename", "uploaded_at")

    def save_model(self, request, obj, form, change):
        # 自動填入原始檔名
        if obj.file and not obj.original_filename:
            obj.original_filename = obj.file.name.split("/")[-1]
        super().save_model(request, obj, form, change)

        # 如果是新建的檔案，自動解析 JSON
        if not change:
            try:
                count = parse_comparison_json(obj)
                self.message_user(request, f"成功解析 {count} 筆比對結果。")
            except Exception as e:
                self.message_user(request, f"JSON 解析失敗: {e}", level="error")


@admin.register(ComparisonEntry)
class ComparisonEntryAdmin(admin.ModelAdmin):
    list_display = ("short_excerpt", "source_page", "is_match", "final_decision_class", "arbitration_status")
    list_filter = ("is_match", "arbitration_status", "comparison_file__project")
    search_fields = ("excerpt_text", "strategy_name", "final_decision_class")
    readonly_fields = (
        "comparison_file", "strategy_name", "excerpt_text", "source_page",
        "reasoning", "is_match", "arbitration_status", "arbitration_note",
        "final_decision_class", "char_start_pos", "char_end_pos",
    )

    def short_excerpt(self, obj):
        return obj.excerpt_text[:60] + "..." if len(obj.excerpt_text) > 60 else obj.excerpt_text
    short_excerpt.short_description = "文字摘錄"


@admin.register(ReviewFeedback)
class ReviewFeedbackAdmin(admin.ModelAdmin):
    list_display = ("entry", "reviewer", "is_correct", "reviewed_at")
    list_filter = ("is_correct", "reviewer")
    search_fields = ("feedback_reason",)
