"""
Django views for GravityPipeCalc app
重力管水理計算視圖
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .utils.type1_flow_table import calculate_flow_table
from .utils.type2_capacity import calculate_capacity_at_depth
from .utils.type3_depth_velocity import calculate_depth_velocity_table
from .utils.type4_slope_table import calculate_slope_table_for_velocity
from .utils.type5_slope_single import calculate_slope_for_velocity_and_flow
from .utils.type6_slope_flow_table import calculate_slope_table_for_flow
from .utils.type7_slope_flow_single import calculate_slope_for_flow_and_depth
from .utils.type8_diameter_recommendation import calculate_recommended_diameter


def home(request):
    """主頁面 - 顯示8種計算類型選擇"""
    return render(request, 'GravityPipeCalc/home.html')


@csrf_exempt
def calculate_type1(request):
    """
    類型一：管線輸送流量表
    輸入：粗糙係數、管徑、坡度
    輸出：各水深比下的流量、流速
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            slope = float(data.get('slope', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or slope <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            results = calculate_flow_table(roughness, diameter, slope)
            
            return JsonResponse({
                'status': 'success',
                'data': results,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter_mm,
                    'slope': slope
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type2(request):
    """
    類型二：特定水深下的輸送容量
    輸入：粗糙係數、管徑、坡度、水深比
    輸出：流速、流量
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            slope = float(data.get('slope', 0))
            depth_ratio = float(data.get('depth_ratio', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or slope <= 0 or depth_ratio <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            if depth_ratio > 1.0:
                return JsonResponse({
                    'status': 'error',
                    'message': '水深比不能大於1.0'
                }, status=400)
            
            result = calculate_capacity_at_depth(roughness, diameter, slope, depth_ratio)
            
            return JsonResponse({
                'status': 'success',
                'data': result,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter_mm,
                    'slope': slope,
                    'depth_ratio': depth_ratio
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type3(request):
    """
    類型三：水深與流速
    輸入：粗糙係數、管徑、坡度、流量
    輸出：各水深比下的流速
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            slope = float(data.get('slope', 0))
            flow_rate = float(data.get('flow_rate', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or slope <= 0 or flow_rate <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            results = calculate_depth_velocity_table(roughness, diameter, slope, flow_rate)
            
            return JsonResponse({
                'status': 'success',
                'data': results,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter_mm,
                    'slope': slope,
                    'flow_rate': flow_rate
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type4(request):
    """
    類型四：維持流速之坡降表
    輸入：粗糙係數、管徑、流速
    輸出：各水深比下的坡度、流量
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            velocity = float(data.get('velocity', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or velocity <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            results = calculate_slope_table_for_velocity(roughness, diameter, velocity)
            
            return JsonResponse({
                'status': 'success',
                'data': results,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter_mm,
                    'velocity': velocity
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type5(request):
    """
    類型五：維持流速之坡降
    輸入：粗糙係數、管徑、流速、流量
    輸出：各水深比下的坡度
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            velocity = float(data.get('velocity', 0))
            flow_rate = float(data.get('flow_rate', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or velocity <= 0 or flow_rate <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            results = calculate_slope_for_velocity_and_flow(
                roughness, diameter, velocity, flow_rate
            )
            
            return JsonResponse({
                'status': 'success',
                'data': results,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter_mm,
                    'velocity': velocity,
                    'flow_rate': flow_rate
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type6(request):
    """
    類型六：輸送流量之坡降表
    輸入：粗糙係數、管徑、流量
    輸出：各水深比下的坡度、流速
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            flow_rate = float(data.get('flow_rate', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or flow_rate <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            results = calculate_slope_table_for_flow(roughness, diameter, flow_rate)
            
            return JsonResponse({
                'status': 'success',
                'data': results,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter_mm,
                    'flow_rate': flow_rate
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type7(request):
    """
    類型七：輸送流量之坡降
    輸入：粗糙係數、管徑、流量、水深比
    輸出：坡度、流速
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            diameter_mm = float(data.get('diameter', 0))
            diameter = diameter_mm / 1000  # 轉換 mm 為 m
            flow_rate = float(data.get('flow_rate', 0))
            depth_ratio = float(data.get('depth_ratio', 0))
            
            if roughness <= 0 or diameter_mm <= 0 or flow_rate <= 0 or depth_ratio <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            if depth_ratio > 1.0:
                return JsonResponse({
                    'status': 'error',
                    'message': '水深比不能大於1.0'
                }, status=400)
            
            result = calculate_slope_for_flow_and_depth(
                roughness, diameter, flow_rate, depth_ratio
            )
            
            return JsonResponse({
                'status': 'success',
                'data': result,
                'input': {
                    'roughness': roughness,
                    'diameter': diameter,
                    'flow_rate': flow_rate,
                    'depth_ratio': depth_ratio
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def calculate_type8(request):
    """
    類型八：建議管徑
    輸入：粗糙係數、流速、流量、水深比
    輸出：建議管徑、坡度
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roughness = float(data.get('roughness', 0))
            velocity = float(data.get('velocity', 0))
            flow_rate = float(data.get('flow_rate', 0))
            depth_ratio = float(data.get('depth_ratio', 0))
            
            if roughness <= 0 or velocity <= 0 or flow_rate <= 0 or depth_ratio <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': '所有參數必須大於0'
                }, status=400)
            
            if depth_ratio > 1.0:
                return JsonResponse({
                    'status': 'error',
                    'message': '水深比不能大於1.0'
                }, status=400)
            
            result = calculate_recommended_diameter(
                roughness, velocity, flow_rate, depth_ratio
            )
            
            return JsonResponse({
                'status': 'success' if result.get('success') else 'error',
                'data': result,
                'input': {
                    'roughness': roughness,
                    'velocity': velocity,
                    'flow_rate': flow_rate,
                    'depth_ratio': depth_ratio
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)
