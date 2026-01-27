from django.urls import path
from . import views

app_name = 'interview_assessment'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Question
    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('questions/categories/', views.CategoryManagerView.as_view(), name='category_list'),
    path('questions/add/', views.QuestionCreateView.as_view(), name='question_add'),
    
    # Quiz
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    path('quizzes/add/', views.QuizCreateView.as_view(), name='quiz_add'),
    path('quizzes/<int:pk>/build/', views.QuizBuilderView.as_view(), name='quiz_builder'),
    
    # Public / Candidate
    path('start/<int:quiz_id>/', views.CandidateEntryView.as_view(), name='quiz_entry'),
    path('exam/<uuid:uuid>/', views.TakeQuizView.as_view(), name='take_quiz'),
    
    # Results
    path('results/', views.ResultListView.as_view(), name='result_list'),
    path('results/<int:pk>/', views.ResultDetailView.as_view(), name='result_detail'),
]
