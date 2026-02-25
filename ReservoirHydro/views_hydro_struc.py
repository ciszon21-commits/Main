"""結構物水理計算平台視圖模組"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


def hydro_structure_app(request):
    """結構物水理主應用頁面"""
    initial_step = request.GET.get("step", "1")

    context = {
        "title": "結構物水理計算模組",
        "initial_step": initial_step,
        "steps": [
            {
                "id": 1,
                "name": "結構物水理計算",
                "icon": "bi-droplet",
                "desc": "輸入參數並執行水理計算",
            },
            {
                "id": 2,
                "name": "圖表成果展示",
                "icon": "bi-bar-chart",
                "desc": "檢視計算結果圖表",
            },
        ],
    }
    return render(request, "hydro_struc/hs_app.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def api_hs_calculation(request):
    """API - 結構物水理計算（回傳水位-流量曲線）"""
    try:
        data = json.loads(request.body)
        # 取得所有輸入參數
        facility_name = data.get("name")
        formula1 = data.get("formula1")
        formula2 = data.get("formula2")
        gate_hole_height = float(data.get("gateHoleHeight", 0))
        gate_hole_width = float(data.get("gateHoleWidth", 0))
        gate_hole_count = int(data.get("gateHoleCount", 0))
        pier_width = float(data.get("pierWidth", 0))
        dam_top_elevation = float(data.get("damTopElevation", 0))
        weir_top_elevation = float(data.get("weirTopElevation", 0))
        sediment_elevation = float(data.get("sedimentElevation", 0))
        max_flood = float(data.get("maxFlood", 0))
        Kp = float(data.get("Kp", 0))
        Ka = float(data.get("Ka", 0))
        L = gate_hole_width * gate_hole_count + pier_width * (gate_hole_count + 1)
        P = weir_top_elevation - sediment_elevation
        H0 = max_flood - weir_top_elevation
        P_divide_H0 = P / H0 if H0 != 0 else 0

        # TODO: 實作水位-流量曲線計算

        # 判斷公式組合
        if formula1 == "free-overflow" and formula2 == "orifice-flow":
            rows = []

            # 水庫水位（wse）
            start = weir_top_elevation
            end = dam_top_elevation
            step = 0.05
            wse = []
            wse.append(round(start, 10))
            next_level = round((int(start * 20) + 1) * step, 10)
            while next_level < end:
                wse.append(round(next_level, 10))
                next_level = round(next_level + step, 10)
            if wse[-1] != round(end, 10):
                wse.append(round(end, 10))

            # 計算 C0（每一列都一樣）
            C0 = 0.552 * (
                -0.1804179809 * P_divide_H0 ** 6 +
                1.4659363764 * P_divide_H0 ** 5 +
                -4.7574750322 * P_divide_H0 ** 4 +
                7.8975531368 * P_divide_H0 ** 3 +
                -7.1553570174 * P_divide_H0 ** 2 +
                3.5180631076 * P_divide_H0 ** 1 +
                3.0964417734
            )

            # 計算每一列
            for w in wse:
                row = {}
                row['WSE'] = w
                row['He'] = round(w - weir_top_elevation, 10)  # 水頭
                row['C0'] = round(C0, 10)
                he_divide_h0 = row['He'] / H0 if H0 != 0 else 0
                row['He/H0'] = round(min(he_divide_h0, 1.6), 10)
                he_h0 = row['He/H0']
                c_divide_c0 = (
                    -0.0300638 * he_h0 ** 6 +
                    0.1665009 * he_h0 ** 5 +
                    -0.3812631 * he_h0 ** 4 +
                    0.4940970 * he_h0 ** 3 +
                    -0.4467989 * he_h0 ** 2 +
                    0.4122024 * he_h0 +
                    0.7838338
                )
                row['C/C0'] = round(c_divide_c0, 10)
                row['L'] = round(L - 2 * (gate_hole_count * Kp + Ka) * row['He'], 10)  # TODO： 需確認這個2是哪來的

                # 判斷是否水位滿過出水口、用孔口流公式
                if w >= weir_top_elevation + gate_hole_height:
                    # 孔口流 Q = CA*sqrt(2gH)
                    C = 0.66  # 暫時係數
                    g = 9.80665
                    A = row['L'] * gate_hole_height
                    Q = C * A * (2 * g * row['He']) ** 0.5
                else:
                    # 原堰流公式
                    Q = row['C0'] * row['C/C0'] * row['L'] * (row['He'] ** 1.5)
                row['Q'] = round(Q, 10)
                row['Qt'] = round(Q * gate_hole_count, 10)
                rows.append(row)
        else:
            # 其他組合，暫不處理
            pass

        result = {
            "success": True,
            "facility_name": facility_name,
            "columns": ["WSE", "He", "C0", "He/H0", "C/C0", "L", "Q", "Qt"],
            "data": rows,
            "message": "計算成功"
        }
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"錯誤：{str(e)}"}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def api_export_hydro_chart(request):
    """API - 匯出計算結果圖表（暫定）"""
    # TODO: 之後補上圖表產生
    return HttpResponse("尚未實作", content_type="text/plain")