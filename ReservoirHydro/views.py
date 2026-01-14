from django.shortcuts import render


def reservoir_hydro_home(request):
    """水庫水文水理計算首頁"""
    context = {
        "title": "水庫水文水理計算平台",
        "description": "涵蓋多樣計算模組，提供完整解決方案。",
    }
    return render(request, "reservoir_hydro_home.html", context)