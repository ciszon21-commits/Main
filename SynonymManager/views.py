from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy
from django.db.models import Count
from django.http import HttpResponse
from .models import SynonymGroup, Keyword
from django.utils import timezone
from StudioBase.constants import SINO_DEPT_DB
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime

# --- Dashboard ---
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'SynonymManager/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 統計資訊
        total_synonyms = SynonymGroup.objects.count()
        total_keywords = Keyword.objects.count()
        
        # 最近更新的 5 筆
        recent_synonyms = SynonymGroup.objects.all().select_related('creator')[:5]
        recent_keywords = Keyword.objects.all().select_related('creator')[:5]
        
        # 1. 依日期統計 (最近 7 天) - 同義詞
        today = timezone.now().date()
        date_labels = []
        synonym_counts = []
        for i in range(6, -1, -1):
            target_date = today - datetime.timedelta(days=i)
            count = SynonymGroup.objects.filter(created_at__date=target_date).count()
            date_labels.append(target_date.strftime('%Y-%m-%d'))
            synonym_counts.append(count)
            
        # 2. 依部門統計 (同義詞)
        dept_stats = SynonymGroup.objects.exclude(creator__isnull=True).values('creator__profile__emp_dept').annotate(total=Count('id')).order_by('-total')
        
        dept_labels = []
        dept_values = []
        for stat in dept_stats:
            dept_code = stat['creator__profile__emp_dept']
            dept_name = SINO_DEPT_DB.get(dept_code, f'未知部門({dept_code})') if dept_code else '未設定部門'
            dept_labels.append(dept_name)
            dept_values.append(stat['total'])

        context['total_synonyms'] = total_synonyms
        context['total_keywords'] = total_keywords
        context['recent_synonyms'] = recent_synonyms
        context['recent_keywords'] = recent_keywords
        context['date_labels'] = date_labels
        context['synonym_counts'] = synonym_counts
        context['dept_labels'] = dept_labels
        context['dept_values'] = dept_values
        return context

# --- Synonym CRUD ---
class SynonymListView(LoginRequiredMixin, ListView):
    model = SynonymGroup
    template_name = 'SynonymManager/list.html'
    context_object_name = 'synonyms'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q')
        qs = SynonymGroup.objects.all().select_related('creator')
        if query:
            return qs.filter(word__icontains=query) | qs.filter(synonym_list__icontains=query)
        return qs

class SynonymCreateView(LoginRequiredMixin, CreateView):
    model = SynonymGroup
    fields = ['word', 'synonym_list']
    template_name = 'SynonymManager/form.html'
    success_url = reverse_lazy('synonyms:list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class SynonymUpdateView(LoginRequiredMixin, UpdateView):
    model = SynonymGroup
    fields = ['word', 'synonym_list']
    template_name = 'SynonymManager/form.html'
    success_url = reverse_lazy('synonyms:list')

class SynonymDeleteView(LoginRequiredMixin, DeleteView):
    model = SynonymGroup
    template_name = 'SynonymManager/confirm_delete.html'
    success_url = reverse_lazy('synonyms:list')

# --- Keyword CRUD ---
class KeywordListView(LoginRequiredMixin, ListView):
    model = Keyword
    template_name = 'SynonymManager/keyword_list.html'
    context_object_name = 'keywords'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q')
        qs = Keyword.objects.all().select_related('creator')
        if query:
            return qs.filter(word__icontains=query)
        return qs

class KeywordCreateView(LoginRequiredMixin, CreateView):
    model = Keyword
    fields = ['word']
    template_name = 'SynonymManager/keyword_form.html'
    success_url = reverse_lazy('synonyms:keyword-list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class KeywordDeleteView(LoginRequiredMixin, DeleteView):
    model = Keyword
    template_name = 'SynonymManager/keyword_confirm_delete.html'
    success_url = reverse_lazy('synonyms:keyword-list')

# --- Export Synonyms ---
class SynonymExportView(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="synonyms_{timezone.now().strftime("%Y%m%d")}.txt"'
        
        queryset = SynonymGroup.objects.all()
        lines = []
        for group in queryset:
            word = group.word.strip()
            synonyms = [s.strip() for s in group.synonym_list.split(',') if s.strip()]
            if synonyms:
                line = f"{word}, {', '.join(synonyms)}"
                lines.append(line)
            else:
                lines.append(word)
        response.write('\n'.join(lines))
        return response

# --- Export Keywords ---
class KeywordExportView(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="keywords_{timezone.now().strftime("%Y%m%d")}.txt"'
        
        queryset = Keyword.objects.all().order_by('word')
        lines = [k.word for k in queryset]
        response.write('\n'.join(lines))
        return response
