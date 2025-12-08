from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Topic, Keyword, NewsItem, DailySummary, Subscription

class TopicListView(ListView):
    model = Topic
    template_name = 'NewsSubscriber/topic_list.html'
    context_object_name = 'topics'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 如果用戶已登入，獲取訂閱狀態
        if self.request.user.is_authenticated:
            subscribed_topics = Subscription.objects.filter(
                user=self.request.user,
                is_active=True
            ).values_list('topic_id', flat=True)
            context['subscribed_topics'] = list(subscribed_topics)
        else:
            context['subscribed_topics'] = []
        return context

class TopicDetailView(DetailView):
    model = Topic
    template_name = 'NewsSubscriber/topic_detail.html'
    context_object_name = 'topic'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent news items (last 50)
        context['news_items'] = self.object.news_items.all()[:50]
        # Get recent summaries (last 7)
        context['summaries'] = self.object.daily_summaries.all()[:7]
        return context

class TopicCreateView(CreateView):
    model = Topic
    fields = ['name']
    template_name = 'NewsSubscriber/topic_form.html'
    success_url = reverse_lazy('news_subscriber:topic_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        # 如果使用者已登入，自動訂閱該主題
        if self.request.user.is_authenticated:
            email = self.request.user.email
            if email:
                # 建立訂閱
                Subscription.objects.create(
                    user=self.request.user,
                    topic=self.object,
                    email=email,
                    is_active=True
                )
                messages.success(
                    self.request,
                    f'成功建立主題「{self.object.name}」並自動訂閱！每日新聞摘要將發送至 {email}'
                )
            else:
                messages.warning(
                    self.request,
                    f'成功建立主題「{self.object.name}」，但您的帳號尚未設定email，無法自動訂閱。請先在個人設定中設定email後再手動訂閱。'
                )
        else:
            messages.success(self.request, f'成功建立主題「{self.object.name}」！')

        return response

class KeywordCreateView(CreateView):
    model = Keyword
    fields = ['word']
    template_name = 'NewsSubscriber/keyword_form.html'

    def form_valid(self, form):
        topic = get_object_or_404(Topic, pk=self.kwargs['topic_id'])
        form.instance.topic = topic
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic'] = get_object_or_404(Topic, pk=self.kwargs['topic_id'])
        return context

    def get_success_url(self):
        return reverse('news_subscriber:topic_detail', kwargs={'pk': self.kwargs['topic_id']})

@login_required
@require_POST
def subscribe_topic(request, topic_id):
    """訂閱主題"""
    topic = get_object_or_404(Topic, pk=topic_id)

    # 使用用戶的email作為接收信箱
    email = request.user.email
    if not email:
        messages.error(request, '您的帳號尚未設定email，無法訂閱。請先在個人設定中設定email。')
        return redirect('news_subscriber:topic_list')

    # 檢查是否已訂閱
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        topic=topic,
        defaults={'email': email, 'is_active': True}
    )

    if not created:
        # 如果已存在但未啟用，則重新啟用
        if not subscription.is_active:
            subscription.is_active = True
            subscription.email = email  # 更新email
            subscription.save()
            messages.success(request, f'已重新訂閱「{topic.name}」！')
        else:
            messages.info(request, f'您已經訂閱了「{topic.name}」。')
    else:
        messages.success(request, f'成功訂閱「{topic.name}」！每日新聞摘要將發送至 {email}')

    return redirect('news_subscriber:topic_list')

@login_required
@require_POST
def unsubscribe_topic(request, topic_id):
    """取消訂閱主題"""
    topic = get_object_or_404(Topic, pk=topic_id)

    try:
        subscription = Subscription.objects.get(
            user=request.user,
            topic=topic
        )
        subscription.is_active = False
        subscription.save()
        messages.success(request, f'已取消訂閱「{topic.name}」。')
    except Subscription.DoesNotExist:
        messages.info(request, f'您尚未訂閱「{topic.name}」。')

    return redirect('news_subscriber:topic_list')
