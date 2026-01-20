from django.contrib import admin
from .models import County, Township, Village, Landmark, GeoQuery


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Township)
class TownshipAdmin(admin.ModelAdmin):
    list_display = ['name', 'county', 'latitude', 'longitude']
    list_filter = ['county']
    search_fields = ['name', 'county__name']
    ordering = ['county', 'name']


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'township', 'get_county', 'latitude', 'longitude']
    list_filter = ['township__county', 'township']
    search_fields = ['name', 'township__name', 'township__county__name']
    ordering = ['township__county', 'township', 'name']
    
    def get_county(self, obj):
        return obj.township.county.name
    get_county.short_description = '縣市'
    get_county.admin_order_field = 'township__county__name'


@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'county', 'township', 'latitude', 'longitude']
    list_filter = ['category', 'county']
    search_fields = ['name', 'aliases', 'county__name']
    ordering = ['county', 'category', 'name']


@admin.register(GeoQuery)
class GeoQueryAdmin(admin.ModelAdmin):
    list_display = ['query_text', 'matched_county', 'matched_township', 'matched_village', 'confidence', 'created_at']
    list_filter = ['matched_county', 'created_at']
    search_fields = ['query_text']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

