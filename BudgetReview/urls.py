from django.urls import path
from . import views

app_name = 'budget_review'

urlpatterns = [
    # Project
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/create-ajax/', views.ProjectCreateAjaxView.as_view(), name='project_create_ajax'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('project/<int:pk>/edit-ajax/', views.ProjectUpdateAjaxView.as_view(), name='project_update_ajax'),
    path('project/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    
    # Discipline
    path('project/<int:project_id>/discipline/create/', views.DisciplineCreateView.as_view(), name='discipline_create'),
    path('project/<int:project_id>/discipline/create-ajax/', views.DisciplineCreateAjaxView.as_view(), name='discipline_create_ajax'),
    path('project/<int:project_id>/discipline/<int:pk>/update-ajax/', views.DisciplineUpdateAjaxView.as_view(), name='discipline_update_ajax'),
    path('project/<int:project_id>/discipline/<int:pk>/edit/', views.DisciplineUpdateView.as_view(), name='discipline_update'),
    path('project/<int:project_id>/discipline/<int:pk>/delete/', views.DisciplineDeleteView.as_view(), name='discipline_delete'),
    
    # File Uploads
    path('project/<int:project_id>/upload/quantity/', views.QuantityFileUploadView.as_view(), name='upload_quantity'),
    path('project/<int:project_id>/upload/quantity-ajax/', views.QuantityFileUploadAjaxView.as_view(), name='upload_quantity_ajax'),
    path('project/<int:project_id>/upload/price_inquiry/', views.PriceInquiryFileUploadView.as_view(), name='upload_price_inquiry'),
    path('project/<int:project_id>/upload/price-inquiry-ajax/', views.PriceInquiryFileUploadAjaxView.as_view(), name='upload_price_inquiry_ajax'),
    path('project/<int:project_id>/upload/budget/', views.BudgetFileUploadView.as_view(), name='upload_budget'),
    path('project/<int:project_id>/upload/budget-ajax/', views.BudgetFileUploadAjaxView.as_view(), name='upload_budget_ajax'),
    path('project/<int:project_id>/upload/final_budget/', views.FinalBudgetFileUploadView.as_view(), name='upload_final_budget'),
    path('project/<int:project_id>/upload/blank-tender-ajax/', views.BlankTenderFileUploadAjaxView.as_view(), name='upload_blank_tender_ajax'),
    
    # File Download
    path('download/<str:file_model>/<int:file_id>/', views.FileDownloadView.as_view(), name='file_download'),
    
    # Price Adjustment
    path('project/<int:project_id>/price_adjustment/create/', views.PriceAdjustmentCreateView.as_view(), name='price_adjustment_create'),
]
