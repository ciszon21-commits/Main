from django.urls import path
from . import views

app_name = 'synonyms'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Synonyms
    path('list/', views.SynonymListView.as_view(), name='list'),
    path('create/', views.SynonymCreateView.as_view(), name='create'),
    path('edit/<int:pk>/', views.SynonymUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.SynonymDeleteView.as_view(), name='delete'),
    path('export/synonyms/', views.SynonymExportView.as_view(), name='export-synonyms'),
    
    # Keywords
    path('keywords/', views.KeywordListView.as_view(), name='keyword-list'),
    path('keywords/create/', views.KeywordCreateView.as_view(), name='keyword-create'),
    path('keywords/delete/<int:pk>/', views.KeywordDeleteView.as_view(), name='keyword-delete'),
    path('export/keywords/', views.KeywordExportView.as_view(), name='export-keywords'),
]
