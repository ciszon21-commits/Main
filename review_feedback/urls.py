from django.urls import path
from . import views

app_name = "review_feedback"

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("create/", views.project_create, name="project_create"),
    path("users/search/", views.user_search, name="user_search"),
    path("<int:project_id>/", views.project_detail, name="project_detail"),
    path("<int:project_id>/edit/", views.project_edit, name="project_edit"),
    path("<int:project_id>/confirmed/", views.project_confirmed_review, name="confirmed_review"),
    path(
        "<int:project_id>/comparison/<int:file_id>/",
        views.comparison_detail,
        name="comparison_detail",
    ),
    path(
        "entry/<int:entry_id>/feedback/",
        views.submit_feedback,
        name="submit_feedback",
    ),
]
