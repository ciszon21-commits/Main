from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # 課程列表與詳情
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    
    # 課程 CRUD
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # 報名相關
    path('<int:pk>/register/', views.register_course, name='register_course'),
    path('<int:pk>/cancel/', views.cancel_registration, name='cancel_registration'),
    path('<int:pk>/registrations/', views.RegistrationListView.as_view(), name='registration_list'),
    
    # PDF 下載
    path('<int:pk>/download-pdf/', views.download_pdf, name='download_pdf'),
]
