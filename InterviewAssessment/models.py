from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class QuestionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="類別名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "題目類別"
        verbose_name_plural = "題目類別"


class Question(models.Model):
    QUESTION_TYPES = (
        ('single', '單選題'),
        ('boolean', '是非題'),
    )
    
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, related_name='questions', verbose_name="類別")
    text = models.TextField(verbose_name="題目內容")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single', verbose_name="題目類型")
    
    # Store choices as a list of strings in JSON, e.g. ["Option A", "Option B", "Option C"]
    # For Boolean, it can be ignored or ["True", "False"]
    choices = models.JSONField(default=list, blank=True, verbose_name="選項 (JSON)")
    
    # Simple string match for correct answer or index
    correct_answer = models.CharField(max_length=255, verbose_name="正確答案")
    
    difficulty = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="難度 (1-5)")
    points = models.IntegerField(default=10, verbose_name="分數")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="建立者")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="啟用中")

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.text[:50]}..."

    class Meta:
        verbose_name = "題目"
        verbose_name_plural = "題目庫"


class Quiz(models.Model):
    title = models.CharField(max_length=200, verbose_name="試卷標題")
    description = models.TextField(blank=True, verbose_name="試卷描述")
    time_limit_minutes = models.IntegerField(default=30, verbose_name="測驗時間 (分鐘)")
    
    questions = models.ManyToManyField(Question, through='QuizQuestion', related_name='quizzes', verbose_name="包含題目")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="建立者")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="啟用中")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "試卷"
        verbose_name_plural = "試卷管理"
        ordering = ['-created_at']


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        ordering = ['order']
        unique_together = ('quiz', 'question')


class Candidate(models.Model):
    name = models.CharField(max_length=100, verbose_name="姓名")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="電話")
    note = models.TextField(blank=True, verbose_name="備註/簡歷")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        verbose_name = "應徵者"
        verbose_name_plural = "應徵者資料"


class QuizAttempt(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='attempts', verbose_name="應徵者")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name="試卷")
    
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="開始時間")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="交卷時間")
    
    score = models.IntegerField(null=True, blank=True, verbose_name="總分")
    max_score = models.IntegerField(null=True, blank=True, verbose_name="滿分")
    
    # Status
    is_completed = models.BooleanField(default=False, verbose_name="已完成")

    @property
    def percentage(self):
        if self.score is not None and self.max_score and self.max_score > 0:
             return round((self.score / self.max_score) * 100, 1)
        return 0

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def __str__(self):
        return f"{self.candidate.name} - {self.quiz.title}"

    class Meta:
        verbose_name = "測驗紀錄"
        verbose_name_plural = "測驗紀錄"
        ordering = ['-start_time']


class Response(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=255, blank=True, verbose_name="選擇答案")
    is_correct = models.BooleanField(default=False, verbose_name="是否正確")

    class Meta:
        verbose_name = "作答明細"
        verbose_name_plural = "作答明細"


class AdminWhitelist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="管理員")
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_whitelist_users')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "管理員白名單"
        verbose_name_plural = "管理員白名單"
