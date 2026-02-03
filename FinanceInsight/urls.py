from django.urls import path
from . import views

app_name = 'finance_insight'

urlpatterns = [
    path('', views.NewsListView.as_view(), name='news_list'),
    path('stocks/', views.StockRecommendationView.as_view(), name='stock_list'),
    path('stocks/update/', views.UpdatePricesView.as_view(), name='update_prices'),
    path('stocks/<int:pk>/', views.StockDetailView.as_view(), name='stock_detail'),
]
