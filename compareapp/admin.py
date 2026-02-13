from django.contrib import admin

from .models import CompareProject, ComparisonMatch, ComparisonRun, GlobalKeyword, ProjectAccess


@admin.register(CompareProject)
class CompareProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_number', 'owner', 'has_budget', 'has_quantity_sheet', 'updated_at')
    list_filter = ('owner',)
    search_fields = ('name', 'plan_number', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ComparisonRun)
class ComparisonRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'created_at', 'finished_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__name', 'project__plan_number')
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'finished_at')


@admin.register(ComparisonMatch)
class ComparisonMatchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'run',
        'method',
        'rank',
        'verdict',
        'score',
        'name_score',
        'updated_at',
    )
    list_filter = ('method', 'verdict', 'created_at')
    search_fields = (
        'left_source_id',
        'right_source_id',
        'left_name',
        'right_name',
        'run__project__name',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GlobalKeyword)
class GlobalKeywordAdmin(admin.ModelAdmin):
    list_display = ('term', 'normalized_term', 'source', 'selected_count', 'is_active', 'updated_at')
    list_filter = ('source', 'is_active', 'created_at')
    search_fields = ('term', 'normalized_term')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProjectAccess)
class ProjectAccessAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'updated_at')
    list_filter = ('role', 'updated_at')
    search_fields = ('project__name', 'project__plan_number', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
