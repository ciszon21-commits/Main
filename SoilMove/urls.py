from django.urls import path
from . import views

app_name = 'SoilMove'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('update_data/', views.UpdateDataView.as_view(), name='update_data'),
    path('api/data/', views.SoilDataAPI.as_view(), name='api_data'),
    path('export/excel/', views.ExportExcelView.as_view(), name='export_excel'),
    path('export/kml/', views.ExportKMLView.as_view(), name='export_kml'),
]
