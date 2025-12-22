from django.contrib import admin
from .models import (
    DevTeam, DevTeamMember, Program, ProgramDatabase,
    FileLocation, DatabaseServer,
    DatabaseDesignDoc, DesignTable, DesignField
)


@admin.register(DatabaseServer)
class DatabaseServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'database_count', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    def database_count(self, obj):
        return obj.databases.count()
    database_count.short_description = "使用數"


class DevTeamMemberInline(admin.TabularInline):
    model = DevTeamMember
    extra = 1
    autocomplete_fields = ['user']


@admin.register(DevTeam)
class DevTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'member_count', 'program_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'created_by__username', 'created_by__first_name']
    autocomplete_fields = ['created_by']
    inlines = [DevTeamMemberInline]
    readonly_fields = ['created_at', 'updated_at']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "成員數"

    def program_count(self, obj):
        return obj.programs.count()
    program_count.short_description = "程式數"


class ProgramDatabaseInline(admin.TabularInline):
    model = ProgramDatabase
    extra = 1
    autocomplete_fields = ['server']


class FileLocationInline(admin.TabularInline):
    model = FileLocation
    extra = 1


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'program_type', 'dev_tool', 'last_modified']
    list_filter = ['program_type', 'team', 'last_modified']
    search_fields = ['name', 'english_name', 'dev_tool', 'team__name', 'developers', 'maintainers']
    autocomplete_fields = ['team']
    inlines = [ProgramDatabaseInline, FileLocationInline]
    readonly_fields = ['created_at', 'last_modified']
    fieldsets = (
        ('基本資訊', {
            'fields': ('team', 'name', 'program_type', 'english_name')
        }),
        ('連結', {
            'fields': ('url', 'git_url')
        }),
        ('開發資訊', {
            'fields': ('dev_tool', 'developers', 'maintainers')
        }),
        ('時間戳記', {
            'fields': ('created_at', 'last_modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProgramDatabase)
class ProgramDatabaseAdmin(admin.ModelAdmin):
    list_display = ['program', 'server', 'database_name', 'table_name', 'access_permission']
    list_filter = ['access_permission', 'server']
    search_fields = ['program__name', 'server__name', 'database_name', 'table_name']
    autocomplete_fields = ['program', 'server']


class DesignTableInline(admin.TabularInline):
    model = DesignTable
    extra = 1
    show_change_link = True


class DesignFieldInline(admin.TabularInline):
    model = DesignField
    extra = 1


@admin.register(DatabaseDesignDoc)
class DatabaseDesignDocAdmin(admin.ModelAdmin):
    list_display = ['name', 'program', 'doc_type', 'table_count', 'updated_at']
    list_filter = ['doc_type', 'program__team']
    search_fields = ['name', 'program__name', 'description']
    inlines = [DesignTableInline]
    readonly_fields = ['created_at', 'updated_at', 'mermaid_content']
    fieldsets = (
        ('基本資訊', {
            'fields': ('program', 'name', 'doc_type', 'description')
        }),
        ('Django Model 模式', {
            'fields': ('django_model_code',),
            'classes': ('collapse',)
        }),
        ('Mermaid 圖表', {
            'fields': ('mermaid_content',),
            'classes': ('collapse',)
        }),
        ('時間戳記', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['parse_django_models', 'regenerate_mermaid']

    def table_count(self, obj):
        return obj.tables.count()
    table_count.short_description = "資料表數"

    def parse_django_models(self, request, queryset):
        for doc in queryset.filter(doc_type='django'):
            doc.parse_django_model()
        self.message_user(request, f"已解析 {queryset.count()} 個文件")
    parse_django_models.short_description = "解析 Django Model"

    def regenerate_mermaid(self, request, queryset):
        for doc in queryset:
            doc.mermaid_content = doc.generate_mermaid()
            doc.save(update_fields=['mermaid_content'])
        self.message_user(request, f"已重新生成 {queryset.count()} 個 Mermaid 圖表")
    regenerate_mermaid.short_description = "重新生成 Mermaid"


@admin.register(DesignTable)
class DesignTableAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'design_doc', 'field_count', 'order']
    list_filter = ['design_doc__program']
    search_fields = ['table_name', 'design_doc__name']
    inlines = [DesignFieldInline]

    def field_count(self, obj):
        return obj.fields.count()
    field_count.short_description = "欄位數"
