"""水庫淤積計算平台視圖模組"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


def siltation_app(request):
    """水庫淤積主應用頁面"""
    initial_step = request.GET.get("step", "1")

    context = {
        "title": "水庫淤積計算模組",
        "initial_step": initial_step,
        "steps": [
            {
                "id": 1,
                "name": "泥沙淤積演算",
                "icon": "bi-calculator",
                "desc": "輸入參數並執行計算",
            },
            {
                "id": 2,
                "name": "圖表成果展示",
                "icon": "bi-bar-chart",
                "desc": "檢視計算結果圖表",
            },
        ],
    }
    return render(request, "siltation/st_app.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def api_run_siltation_calculation(request):
    """API - 執行計算（暫定）"""
    # TODO: 之後補上實際計算
    return JsonResponse({"success": True, "message": "計算已執行（暫定）"})


@csrf_exempt
@require_http_methods(["GET"])
def api_export_siltation_chart(request):
    """API - 匯出計算結果圖表（暫定）"""
    # TODO: 之後補上圖表產生
    return HttpResponse("尚未實作", content_type="text/plain")