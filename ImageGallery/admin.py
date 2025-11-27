from django.contrib import admin
from .models import ImageCategory, Image, ImageRating


@admin.register(ImageCategory)
class ImageCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'created_by', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'uploaded_by', 'uploaded_at', 'view_count', 'get_average_rating', 'get_total_ratings']
    list_filter = ['category', 'uploaded_at']
    search_fields = ['title', 'description', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'view_count']
    date_hierarchy = 'uploaded_at'
    
    def get_average_rating(self, obj):
        return obj.average_rating
    get_average_rating.short_description = '平均評分'
    
    def get_total_ratings(self, obj):
        return obj.total_ratings
    get_total_ratings.short_description = '評分數'


@admin.register(ImageRating)
class ImageRatingAdmin(admin.ModelAdmin):
    list_display = ['image', 'user', 'rating', 'created_at', 'updated_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['image__title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
