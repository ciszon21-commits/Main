"""
水理分析抽水預測系統 Views
"""
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import (
    compute_required_Q,
    generate_contour,
    build_result_table,
)


def home(request):
    """主頁面"""
    return render(request, 'WellDrawdown/home.html')


@csrf_exempt
@require_POST
def calculate(request):
    """
    接收 JSON 參數，計算各井抽水量並回傳 contour 圖 + 結果表。
    """
    try:
        data = json.loads(request.body)

        # 方法選擇
        method = data.get('method', 'theis')  # 'theis', 'neuman', 'both'

        # 基本參數
        params = {
            'T': float(data.get('T', 600)),           # 導水係數 m²/day
            'S': float(data.get('S', 0.001)),          # 貯水係數
            't': float(data.get('t', 4)),              # 抽水時間 day
            'excavation_depth': float(data.get('excavation_depth', 21.6)),  # 開挖深度 m
            'head': float(data.get('head', 36)),       # 水頭 m
        }

        # Neuman 額外參數
        if method in ('neuman', 'both'):
            params['Sy'] = float(data.get('Sy', 0.20))
            params['Kh'] = float(data.get('Kh', 200))
            params['Kv'] = float(data.get('Kv', 20))
            params['b'] = float(data.get('b', 60))

        # 井位座標
        wells_raw = data.get('wells', [])
        wells = [(float(w['x']), float(w['y'])) for w in wells_raw]

        # 車站外框座標
        station_raw = data.get('station_coords', [])
        station_coords = [(float(s['x']), float(s['y'])) for s in station_raw]

        if len(wells) == 0:
            return JsonResponse({'error': '至少需要一口抽水井'}, status=400)
        if len(station_coords) < 3:
            return JsonResponse({'error': '車站外框至少需要3個點位'}, status=400)

        response_data = {}

        if method == 'theis' or method == 'both':
            # Theis 計算
            Q_list_theis = compute_required_Q(wells, station_coords, params, method='theis')
            contour_theis = generate_contour(wells, Q_list_theis, station_coords, params, method='theis')
            table_theis = build_result_table(wells, Q_list_theis)
            response_data['theis'] = {
                'contour': contour_theis,
                'table': table_theis,
                'Q_list': [round(q, 1) for q in Q_list_theis],
            }

        if method == 'neuman' or method == 'both':
            # Neuman 計算
            Q_list_neuman = compute_required_Q(wells, station_coords, params, method='neuman')
            contour_neuman = generate_contour(wells, Q_list_neuman, station_coords, params, method='neuman')
            table_neuman = build_result_table(wells, Q_list_neuman)
            response_data['neuman'] = {
                'contour': contour_neuman,
                'table': table_neuman,
                'Q_list': [round(q, 1) for q in Q_list_neuman],
            }

        return JsonResponse({'success': True, 'data': response_data})

    except json.JSONDecodeError:
        return JsonResponse({'error': '無效的 JSON 資料'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'計算錯誤: {str(e)}'}, status=500)


def forward_page(request):
    """正算模式頁面"""
    return render(request, 'WellDrawdown/forward.html')


@csrf_exempt
@require_POST
def calculate_forward(request):
    """
    接收 JSON 參數 (含固定的抽水井 Q 值)，直接產生 contour 圖與結果。
    不進行反推最佳化。
    """
    try:
        data = json.loads(request.body)

        method = data.get('method', 'theis')

        params = {
            'T': float(data.get('T', 600)),
            'S': float(data.get('S', 0.001)),
            't': float(data.get('t', 4)),
            'excavation_depth': float(data.get('excavation_depth', 0)), # 正算不強制需要開挖深度，但保留給圖表顯示用
            'head': float(data.get('head', 36)),
        }

        if method in ('neuman', 'both'):
            params['Sy'] = float(data.get('Sy', 0.20))
            params['Kh'] = float(data.get('Kh', 200))
            params['Kv'] = float(data.get('Kv', 20))
            params['b'] = float(data.get('b', 60))

        # 井位座標與自訂的抽水量 Q
        wells_raw = data.get('wells', [])
        # 這裡的 Q 是 CMD
        wells = [(float(w['x']), float(w['y'])) for w in wells_raw]
        Q_list = [float(w.get('q', 0)) for w in wells_raw]

        station_raw = data.get('station_coords', [])
        station_coords = [(float(s['x']), float(s['y'])) for s in station_raw]

        if len(wells) == 0:
            return JsonResponse({'error': '至少需要一口抽水井'}, status=400)

        response_data = {}

        if method == 'theis' or method == 'both':
            contour_theis = generate_contour(wells, Q_list, station_coords, params, method='theis')
            table_theis = build_result_table(wells, Q_list)
            response_data['theis'] = {
                'contour': contour_theis,
                'table': table_theis,
                'Q_list': [round(q, 1) for q in Q_list],
            }

        if method == 'neuman' or method == 'both':
            contour_neuman = generate_contour(wells, Q_list, station_coords, params, method='neuman')
            table_neuman = build_result_table(wells, Q_list)
            response_data['neuman'] = {
                'contour': contour_neuman,
                'table': table_neuman,
                'Q_list': [round(q, 1) for q in Q_list],
            }

        return JsonResponse({'success': True, 'data': response_data})

    except json.JSONDecodeError:
        return JsonResponse({'error': '無效的 JSON 資料'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'正算錯誤: {str(e)}'}, status=500)

