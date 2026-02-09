from django.contrib import admin
from .models import (
    NewsCategory, 
    FinancialNews, 
    DailyNewsSummary, 
    StockMarket, 
    StockRecommendation, 
    StockTrend
)


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['code']


@admin.register(FinancialNews)
class FinancialNewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'source', 'published_at', 'fetched_at']
    search_fields = ['title', 'content', 'source']
    list_filter = ['category', 'source', 'published_at']
    date_hierarchy = 'published_at'


@admin.register(DailyNewsSummary)
class DailyNewsSummaryAdmin(admin.ModelAdmin):
    list_display = ['category', 'date', 'news_count', 'created_at']
    search_fields = ['summary', 'conclusion']
    list_filter = ['category', 'date']
    date_hierarchy = 'date'


@admin.register(StockMarket)
class StockMarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country']
    search_fields = ['name', 'code', 'country']
    list_filter = ['country']


class StockTrendInline(admin.TabularInline):
    model = StockTrend
    extra = 1


@admin.register(StockRecommendation)
class StockRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'stock_code', 
        'stock_name', 
        'market', 
        'current_price', 
        'price_change_percent', 
        'recommendation_date'
    ]
    search_fields = ['stock_code', 'stock_name', 'recommendation_reason']
    list_filter = ['market', 'recommendation_date']
    date_hierarchy = 'recommendation_date'
    inlines = [StockTrendInline]


@admin.register(StockTrend)
class StockTrendAdmin(admin.ModelAdmin):
    list_display = ['stock', 'analysis_date', 'created_at']
    search_fields = ['trend_description', 'stock__stock_name', 'stock__stock_code']
    list_filter = ['analysis_date', 'stock__market']
    date_hierarchy = 'analysis_date'
