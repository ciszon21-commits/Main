from django.urls import path
from . import views
from . import views_flood
from . import views_hydro_struc
from . import views_siltation

app_name = "reservoir_hydro"

urlpatterns = [
    path("", views.reservoir_hydro_home, name="reservoir_hydro_home"),  # 水文水理計算主頁面

    # 三大計算功能頁面
    path("flood-drainage/", views_flood.flood_drainage_app, name="flood_drainage_app"),      # 排洪演算
    path("hydro-structure/", views_hydro_struc.hydro_structure_app, name="hydro_structure_app"),  # 結構物水理
    path("siltation/", views_siltation.siltation_app, name="siltation_app"),            # 水庫淤積

    # Flood Drainage API
    path("flood-drainage/api/upload/", views_flood.api_upload, name="api_upload"),
    path("flood-drainage/api/save/", views_flood.api_save, name="api_save"),
    path("flood-drainage/api/export-chart/", views_flood.export_chart, name="export_chart"),
    path("flood-drainage/api/adjust-inflow/", views_flood.api_adjust_inflow, name="api_adjust_inflow"),
    path("flood-drainage/api/adjustment-info/", views_flood.api_get_adjustment_info, name="api_get_adjustment_info"),
    path("flood-drainage/api/run/", views_flood.api_run_flood_calculation, name="api_run_flood_calculation"),
    path("flood-drainage/api/run-simple/", views_flood.api_run_flood_calculation_simple, name="api_run_flood_calculation_simple"),
    path("flood-drainage/api/run-flood-calculation/", views_flood.api_run_flood_calculation, name="api_run_flood_calculation"),

    # Hydro Structure API
    path("hydro-structure/api/hs_calculation/", views_hydro_struc.api_hs_calculation, name="api_hs_calculation"),
]
