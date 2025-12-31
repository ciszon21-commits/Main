from django.urls import path
from . import views

app_name = 'news_subscriber'

urlpatterns = [
    path('', views.TopicListView.as_view(), name='topic_list'),
    path('topic/add/', views.TopicCreateView.as_view(), name='topic_add'),
    path('topic/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topic/<int:topic_id>/keyword/add/', views.KeywordCreateView.as_view(), name='keyword_add'),
    path('topic/<int:topic_id>/subscribe/', views.subscribe_topic, name='subscribe_topic'),
    path('topic/<int:topic_id>/unsubscribe/', views.unsubscribe_topic, name='unsubscribe_topic'),
    path('topic/<int:topic_id>/fetch/', views.fetch_topic_news, name='fetch_topic_news'),
]
