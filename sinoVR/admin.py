from django.contrib import admin
from .models import Scene, Panorama, Asset3D, SceneObject

class SceneObjectInline(admin.TabularInline):
    model = SceneObject
    extra = 0

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    inlines = [SceneObjectInline]

@admin.register(Panorama)
class PanoramaAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')

@admin.register(Asset3D)
class Asset3DAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')

@admin.register(SceneObject)
class SceneObjectAdmin(admin.ModelAdmin):
    list_display = ('scene', 'asset', 'position_x', 'position_y', 'position_z')
    list_filter = ('scene',)
