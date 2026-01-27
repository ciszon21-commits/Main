from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Avg, Count
from django.utils import timezone

from .models import Question, Quiz, Candidate, QuizAttempt, Response, AdminWhitelist, QuestionCategory, QuizQuestion
from .forms import QuestionForm, QuizForm, CandidateForm

class WhitelistRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return AdminWhitelist.objects.filter(user=user).exists()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'InterviewAssessment/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_attempts'] = QuizAttempt.objects.order_by('-start_time')[:5]
        context['questions_count'] = Question.objects.count()
        context['quizzes_count'] = Quiz.objects.count()
        context['candidates_count'] = Candidate.objects.count()
        return context

# --- Question Management ---
class QuestionListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = 'InterviewAssessment/question_list.html'
    context_object_name = 'questions'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset().order_by('-id')
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = QuestionCategory.objects.all()
        return context

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'InterviewAssessment/question_form.html'
    success_url = reverse_lazy('interview_assessment:question_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "題目已建立")
        return super().form_valid(form)

class CategoryManagerView(LoginRequiredMixin, View):
    template_name = 'InterviewAssessment/category_list.html'

    def get(self, request, *args, **kwargs):
        categories = QuestionCategory.objects.annotate(q_count=Count('questions'))
        return render(request, self.template_name, {'categories': categories})

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            QuestionCategory.objects.get_or_create(name=name, defaults={'description': description})
            messages.success(request, f"類別 '{name}' 已建立")
        return redirect('interview_assessment:category_list')

# --- Quiz Management ---
class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'InterviewAssessment/quiz_list.html'
    context_object_name = 'quizzes'

class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'InterviewAssessment/quiz_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        quiz = form.save()
        messages.success(self.request, "試卷已建立，請選擇題目")
        return redirect('interview_assessment:quiz_builder', pk=quiz.pk)

class QuizBuilderView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'InterviewAssessment/quiz_builder.html'
    context_object_name = 'quiz'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # All active questions grouping by category
        context['categories'] = QuestionCategory.objects.prefetch_related('questions').all()
        context['selected_question_ids'] = list(self.object.questions.values_list('id', flat=True))
        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        selected_ids = request.POST.getlist('question_ids')
        
        # Clear existing and add new (Simple Toggle Logic)
        QuizQuestion.objects.filter(quiz=quiz).delete()
        
        for q_id in selected_ids:
            QuizQuestion.objects.create(quiz=quiz, question_id=q_id)
            
        messages.success(request, "試卷題目已更新")
        return redirect('interview_assessment:quiz_list')

# --- Assessment (Public/Candidate) ---
class CandidateEntryView(CreateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'InterviewAssessment/candidate_entry.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=self.kwargs.get('quiz_id'))
        if not self.quiz.is_active:
             return render(request, 'InterviewAssessment/error.html', {'message': '此測驗已關閉'})
        return super().dispatch(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.quiz
        return context
        
    def form_valid(self, form):
        candidate = form.save()
        # Create Attempt
        attempt = QuizAttempt.objects.create(
            candidate=candidate,
            quiz=self.quiz,
        )
        # Redirect to start
        return redirect('interview_assessment:take_quiz', uuid=attempt.uuid)

class TakeQuizView(DetailView):
    model = QuizAttempt
    template_name = 'InterviewAssessment/take_quiz.html'
    context_object_name = 'attempt'
    slug_url_kwarg = 'uuid'
    slug_field = 'uuid'
    
    def dispatch(self, request, *args, **kwargs):
        attempt = self.get_object()
        if attempt.is_completed:
            return render(request, 'InterviewAssessment/completed.html', {'attempt': attempt})
        
        # Check time limit
        if attempt.quiz.time_limit_minutes > 0:
            elapsed = (timezone.now() - attempt.start_time).total_seconds() / 60
            if elapsed > attempt.quiz.time_limit_minutes:
                # Time over
                return self.finish_exam(attempt)
                
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch questions ordered by the link order
        context['questions'] = self.object.quiz.questions.order_by('quizquestion__order')
        return context

    def post(self, request, *args, **kwargs):
        attempt = self.get_object()
        questions = attempt.quiz.questions.all()
        
        score = 0
        total_possible = 0
        
        for q in questions:
            user_ans = request.POST.get(f'question_{q.id}')
            is_correct = False
            
            # Simple exact string match
            if user_ans and user_ans.strip() == q.correct_answer.strip():
                is_correct = True
                score += q.points
            
            total_possible += q.points
            
            Response.objects.create(
                attempt=attempt,
                question=q,
                selected_answer=user_ans if user_ans else "",
                is_correct=is_correct
            )
            
        attempt.score = score
        attempt.max_score = total_possible
        attempt.end_time = timezone.now()
        attempt.is_completed = True
        attempt.save()
        
        return redirect('interview_assessment:take_quiz', uuid=attempt.uuid)

    def finish_exam(self, attempt):
         if not attempt.is_completed:
             attempt.end_time = timezone.now()
             attempt.is_completed = True
             attempt.save()
         return render(self.request, 'InterviewAssessment/completed.html', {'attempt': attempt})

# --- Admin Result Views ---
class ResultListView(LoginRequiredMixin, ListView):
    model = QuizAttempt
    template_name = 'InterviewAssessment/result_list.html'
    context_object_name = 'attempts'
    ordering = ['-start_time']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(quiz__created_by=user)
        return qs

class ResultDetailView(LoginRequiredMixin, DetailView):
    model = QuizAttempt
    template_name = 'InterviewAssessment/result_detail.html'
    context_object_name = 'attempt'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if not user.is_superuser:
            if obj.quiz.created_by != user:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You do not have permission to view this result.")
        return obj
