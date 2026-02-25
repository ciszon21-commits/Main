from django.urls import path

from . import views


app_name = "design_consistency"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("project/<int:project_id>/", views.project_detail, name="project_detail"),
    path("project/<int:project_id>/export-stats/", views.export_stats, name="export_stats"),
    path("matrix/", views.matrix, name="matrix"),
    path("report/<int:run_id>/", views.report_detail, name="report_detail"),
    path("preview/xls/", views.preview_xls, name="preview_xls"),
    path("preview/xml/", views.preview_xml, name="preview_xml"),
]

