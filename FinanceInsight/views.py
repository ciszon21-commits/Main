from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from .models import NewsCategory, FinancialNews, DailyNewsSummary, StockMarket, StockRecommendation
from .utils.stock_fetcher import update_all_stock_prices


class NewsListView(ListView):
    """財經新聞列表"""
    model = NewsCategory
    template_name = 'FinanceInsight/news_list.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # 取得各分類的當日摘要
        context['daily_summaries'] = {
            summary.category_id: summary 
            for summary in DailyNewsSummary.objects.filter(date=today)
        }
        
        # 取得各分類的最新新聞
        context['recent_news'] = {}
        for category in context['categories']:
            context['recent_news'][category.id] = category.news_items.all()[:5]
        
        context['today'] = today
        return context


class StockRecommendationView(ListView):
    """選股建議列表"""
    model = StockMarket
    template_name = 'FinanceInsight/stock_recommendations.html'
    context_object_name = 'markets'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # 取得各股市的選股建議
        context['recommendations'] = {}
        for market in context['markets']:
            recommendations = market.recommendations.filter(
                recommendation_date=today
            ).prefetch_related('trends')
            
            # 如果今天沒有，取最近的
            if not recommendations.exists():
                recommendations = market.recommendations.all()[:10]
            
            context['recommendations'][market.id] = recommendations
        
        context['today'] = today
        return context


class StockDetailView(DetailView):
    """個股詳情"""
    model = StockRecommendation
    template_name = 'FinanceInsight/stock_detail.html'
    context_object_name = 'stock'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 取得個股的歷史趨勢
        context['trends'] = self.object.trends.all()
        return context

class UpdatePricesView(View):
    """更新股價 View"""
    def get(self, request, *args, **kwargs):
        try:
            results = update_all_stock_prices()
            success_count = results.get('success', 0)
            simulated_count = results.get('simulated', 0)
            failed_count = results.get('failed', 0)
            
            msg = f"更新完成！成功: {success_count}"
            if simulated_count > 0:
                msg += f", 模擬更新: {simulated_count} (因網路限制)"
            if failed_count > 0:
                msg += f", 失敗: {failed_count}"
                
            if success_count > 0 or simulated_count > 0:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)
        except Exception as e:
            messages.error(request, f"更新失敗: {str(e)}")
            
        return redirect('finance_insight:stock_list')
