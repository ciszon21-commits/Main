from django.contrib import admin
from .models import WeatherStation, MonthlyReport


@admin.register(WeatherStation)
class WeatherStationAdmin(admin.ModelAdmin):
    list_display = ['station_code', 'name', 'city', 'region', 'altitude', 'established_date']
    list_filter = ['city', 'region']
    search_fields = ['station_code', 'name', 'city']
    ordering = ['station_code']


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ['station', 'obs_date', 'temperature', 'max_temperature', 'min_temperature', 'precipitation']
    list_filter = ['station', 'obs_date']
    search_fields = ['station__name', 'station__station_code']
    date_hierarchy = 'obs_date'
    ordering = ['-obs_date']
