from django.urls import path

from .views import (
    compare_match_annotation_view,
    compare_run_status_view,
    budget_terms_view,
    budget_upload_view,
    compare_view,
    compare_view_structured,
    compare_view_fluid,
    compare_view_apple,
    project_detail_view,
    project_index_view,
    quantity_upload_view,
    keyword_add_view,
    global_keyword_manage_view,
    project_access_manage_view,
    # Apple Views
    project_index_apple_view,
    project_detail_apple_view,
    budget_upload_apple_view,
    budget_terms_apple_view,
    quantity_upload_apple_view,
)

app_name = 'compareapp'

urlpatterns = [
    path('', project_index_view, name='project_index'),
    path('keywords/global/', global_keyword_manage_view, name='global_keyword_manage'),
    path('projects/<int:project_id>/', project_detail_view, name='project_detail'),
    path('projects/<int:project_id>/access/', project_access_manage_view, name='project_access_manage'),
    path('projects/<int:project_id>/budget/upload/', budget_upload_view, name='budget_upload'),
    path('projects/<int:project_id>/budget/terms/', budget_terms_view, name='budget_terms'),
    path('projects/<int:project_id>/quantity/upload/', quantity_upload_view, name='quantity_upload'),
    path('projects/<int:project_id>/compare/', compare_view, name='compare'),
    path('projects/<int:project_id>/compare/structured/', compare_view_structured, name='compare_structured'),
    path('projects/<int:project_id>/compare/fluid/', compare_view_fluid, name='compare_fluid'),
    path('projects/<int:project_id>/compare/apple/', compare_view_apple, name='compare_apple'),
    path(
        'projects/<int:project_id>/compare/runs/<int:run_id>/status/',
        compare_run_status_view,
        name='compare_run_status',
    ),
    path(
        'projects/<int:project_id>/compare/runs/<int:run_id>/matches/<int:match_id>/annotation/',
        compare_match_annotation_view,
        name='compare_match_annotation',
    ),
    path(
        'projects/<int:project_id>/keywords/add/',
        keyword_add_view,
        name='keyword_add',
    ),

    # Apple Flow
    path('apple/', project_index_apple_view, name='project_index_apple'),
    path('apple/projects/<int:project_id>/', project_detail_apple_view, name='project_detail_apple'),
    path('apple/projects/<int:project_id>/budget/upload/', budget_upload_apple_view, name='budget_upload_apple'),
    path('apple/projects/<int:project_id>/budget/terms/', budget_terms_apple_view, name='budget_terms_apple'),
    path('apple/projects/<int:project_id>/quantity/upload/', quantity_upload_apple_view, name='quantity_upload_apple'),
]
