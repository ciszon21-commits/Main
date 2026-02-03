from django.contrib import admin
from .models import SoilMove

@admin.register(SoilMove)
class SoilMoveAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'site_type', 'remain_capacity', 'apply_date')
    search_fields = ('name', 'city', 'site_type')
    list_filter = ('city', 'site_type')
