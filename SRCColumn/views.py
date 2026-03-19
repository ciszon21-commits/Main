"""
SRC柱設計 Django Views
"""
import json

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .utils.calculation import calculate_src_column
from .utils.docx_generator import generate_docx


def home(request):
    """主頁面"""
    return render(request, 'SRCColumn/home.html')


@csrf_exempt
def calculate(request):
    """
    計算 API
    POST JSON → 回傳完整計算結果
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)

        result = calculate_src_column(
            col_B=int(data['col_B']),
            col_H=int(data['col_H']),
            col_length=float(data['col_length']),
            steel_b=int(data['steel_b']),
            steel_h=int(data['steel_h']),
            steel_t=int(data['steel_t']),
            rebar_config=data['rebar_config'],
            rebar_size=data['rebar_size'],
            cover_d=float(data['cover_d']),
            rebar_spacing=float(data['rebar_spacing']),
            kx=float(data['kx']),
            ky=float(data['ky']),
            fys=int(data['fys']),
            steel_grade=data['steel_grade'],
            fyr=int(data['fyr']),
            fc=int(data['fc']),
            pu=float(data['pu']),
            mux=float(data['mux']),
            muy=float(data['muy']),
        )

        return JsonResponse({'status': 'success', 'data': result})

    except KeyError as e:
        return JsonResponse({'status': 'error', 'message': f'缺少參數: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def download_docx(request):
    """
    產生並下載 Word 文件
    POST JSON → 回傳 .docx 文件
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)

        result = calculate_src_column(
            col_B=int(data['col_B']),
            col_H=int(data['col_H']),
            col_length=float(data['col_length']),
            steel_b=int(data['steel_b']),
            steel_h=int(data['steel_h']),
            steel_t=int(data['steel_t']),
            rebar_config=data['rebar_config'],
            rebar_size=data['rebar_size'],
            cover_d=float(data['cover_d']),
            rebar_spacing=float(data['rebar_spacing']),
            kx=float(data['kx']),
            ky=float(data['ky']),
            fys=int(data['fys']),
            steel_grade=data['steel_grade'],
            fyr=int(data['fyr']),
            fc=int(data['fc']),
            pu=float(data['pu']),
            mux=float(data['mux']),
            muy=float(data['muy']),
        )

        buffer = generate_docx(result)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = 'attachment; filename="SRC_Column_Design_Report.docx"'
        return response

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
