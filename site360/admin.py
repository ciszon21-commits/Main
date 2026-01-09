from django.contrib import admin
from .models import Project, Scene

class SceneInline(admin.TabularInline):
    model = Scene
    extra = 1
    fields = ('title', 'image', 'order', 'pitch', 'yaw', 'hfov')
    ordering = ('order',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'scene_count')
    search_fields = ('name', 'description')
    inlines = [SceneInline]

    def scene_count(self, obj):
        return obj.scenes.count()
    scene_count.short_description = "場景數量"

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'order', 'preview_image')
    list_filter = ('project',)
    search_fields = ('title', 'project__name')
    ordering = ('project', 'order')

    def preview_image(self, obj):
        if obj.image:
            return "有圖片"
        return "無圖片"
    preview_image.short_description = "圖片"
