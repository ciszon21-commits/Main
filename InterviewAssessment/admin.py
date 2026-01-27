from django.contrib import admin
from .models import (
    QuestionCategory, Question, Quiz, QuizQuestion, 
    Candidate, QuizAttempt, Response, AdminWhitelist
)

class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1

@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'category', 'question_type', 'difficulty', 'points', 'is_active')
    list_filter = ('category', 'question_type', 'difficulty', 'is_active')
    search_fields = ('text',)

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'time_limit_minutes', 'created_by', 'created_at', 'is_active')
    inlines = [QuizQuestionInline]
    list_filter = ('is_active',)
    search_fields = ('title',)

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'quiz', 'start_time', 'end_time', 'score', 'is_completed')
    list_filter = ('is_completed', 'quiz')

@admin.register(AdminWhitelist)
class AdminWhitelistAdmin(admin.ModelAdmin):
    list_display = ('user', 'added_by', 'created_at')
