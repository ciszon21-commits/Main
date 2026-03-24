from django.contrib import admin
from .models import FoundationExcavation


@admin.register(FoundationExcavation)
class FoundationExcavationAdmin(admin.ModelAdmin):
    list_display = ('project_code', 'bridge_name', 'bridge_id', 'column_base_el', 'h1_thickness', 'created_at')
    list_filter = ('project_code', 'bridge_name')
    search_fields = ('project_code', 'bridge_name', 'bridge_id')
