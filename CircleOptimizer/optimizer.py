"""
圓優化算法模組
提供3心圓和4心圓的最小化覆蓋優化功能
"""
import numpy as np
from scipy.optimize import minimize, differential_evolution
import math


def point_in_circle(point, center_x, center_y, radius):
    """
    檢查點是否在圓內
    
    Args:
        point: [x, y] 座標
        center_x: 圓心X座標
        center_y: 圓心Y座標
        radius: 半徑
    
    Returns:
        bool: True 如果點在圓內或圓上
    """
    distance = np.sqrt((point[0] - center_x)**2 + (point[1] - center_y)**2)
    return distance <= radius + 1e-6  # 加入小容差


def check_coverage(points, circles):
    """
    檢查所有點是否被至少一個圓覆蓋
    
    Args:
        points: 點的陣列 [[x1,y1], [x2,y2], ...]
        circles: 圓的陣列，每個圓為 [cx, cy, r]
    
    Returns:
        bool: True 如果所有點都被覆蓋
    """
    for point in points:
        covered = False
        for circle in circles:
            cx, cy, r = circle
            if point_in_circle(point, cx, cy, r):
                covered = True
                break
        if not covered:
            return False
    return True


def calculate_circle_area(radius):
    """計算圓的面積"""
    return math.pi * radius**2


def calculate_total_area(circles):
    """
    計算多個圓的總面積（簡化版本：不考慮重疊）
    
    Args:
        circles: 圓的陣列，每個圓為 [cx, cy, r]
    
    Returns:
        float: 總面積
    """
    total = 0
    for circle in circles:
        _, _, r = circle
        total += calculate_circle_area(r)
    return total


def objective_function(params, points, num_circles):
    """
    優化目標函數：最小化總面積，同時確保所有點被覆蓋
    
    Args:
        params: 優化參數 [x1, y1, r1, x2, y2, r2, ...]
        points: 控制點陣列
        num_circles: 圓的數量
    
    Returns:
        float: 目標值（面積 + 懲罰項）
    """
    circles = []
    for i in range(num_circles):
        cx = params[i*3]
        cy = params[i*3 + 1]
        r = params[i*3 + 2]
        circles.append([cx, cy, r])
    
    # 計算總面積
    area = calculate_total_area(circles)
    
    # 檢查覆蓋約束，對未覆蓋的點添加懲罰
    penalty = 0
    for point in points:
        covered = False
        for circle in circles:
            cx, cy, r = circle
            if point_in_circle(point, cx, cy, r):
                covered = True
                break
        if not covered:
            # 計算點到最近圓的距離作為懲罰
            min_dist = float('inf')
            for circle in circles:
                cx, cy, r = circle
                dist = np.sqrt((point[0] - cx)**2 + (point[1] - cy)**2) - r
                min_dist = min(min_dist, max(0, dist))
            penalty += 1000 * (min_dist**2)  # 大懲罰確保滿足約束
    
    return area + penalty


def get_initial_bounds(points):
    """
    根據控制點計算初始邊界
    
    Args:
        points: 控制點陣列
    
    Returns:
        tuple: (min_x, max_x, min_y, max_y)
    """
    points_array = np.array(points)
    min_x = points_array[:, 0].min()
    max_x = points_array[:, 0].max()
    min_y = points_array[:, 1].min()
    max_y = points_array[:, 1].max()
    
    return min_x, max_x, min_y, max_y


def optimize_circles(points, num_circles):
    """
    優化圓配置以最小化總面積
    
    Args:
        points: 控制點陣列 [[x1,y1], [x2,y2], ...]
        num_circles: 圓的數量（3或4）
    
    Returns:
        dict: 包含優化結果的字典
    """
    points = np.array(points)
    min_x, max_x, min_y, max_y = get_initial_bounds(points)
    
    # 計算初始半徑估計（覆蓋所有點的圓半徑）
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    max_radius = max([np.sqrt((p[0] - center_x)**2 + (p[1] - center_y)**2) for p in points])
    
    # 設置邊界：每個圓 (cx, cy, r)
    bounds = []
    for i in range(num_circles):
        bounds.append((min_x - max_radius, max_x + max_radius))  # cx
        bounds.append((min_y - max_radius, max_y + max_radius))  # cy
        bounds.append((0.1, max_radius * 2))  # r (半徑必須大於0)
    
    # 使用差分進化算法進行全局優化
    result = differential_evolution(
        objective_function,
        bounds,
        args=(points, num_circles),
        maxiter=300,
        popsize=15,
        seed=42,
        atol=1e-4,
        tol=1e-4
    )
    
    # 解析結果
    circles = []
    for i in range(num_circles):
        cx = result.x[i*3]
        cy = result.x[i*3 + 1]
        r = result.x[i*3 + 2]
        circles.append({
            'center_x': float(cx),
            'center_y': float(cy),
            'radius': float(r),
            'circle_index': i
        })
    
    total_area = calculate_total_area([[c['center_x'], c['center_y'], c['radius']] for c in circles])
    
    # 為每個圓計算弧長和角度（簡化版本）
    for circle in circles:
        arc_data = calculate_arc_params(
            circle['center_x'],
            circle['center_y'],
            circle['radius'],
            points
        )
        circle.update(arc_data)
    
    return {
        'success': result.success,
        'circles': circles,
        'total_area': float(total_area),
        'message': result.message if hasattr(result, 'message') else 'Optimization completed'
    }


def calculate_arc_params(cx, cy, radius, points):
    """
    計算圓弧參數（弧長、起始角度、結束角度）
    
    Args:
        cx: 圓心X座標
        cy: 圓心Y座標
        radius: 半徑
        points: 所有控制點
    
    Returns:
        dict: 包含 arc_length, start_angle, end_angle
    """
    # 找出在這個圓內的點
    covered_points = []
    for point in points:
        if point_in_circle(point, cx, cy, radius):
            covered_points.append(point)
    
    if len(covered_points) == 0:
        # 如果沒有點被覆蓋，返回完整圓
        return {
            'arc_length': 2 * math.pi * radius,
            'start_angle': 0.0,
            'end_angle': 360.0
        }
    
    # 計算每個被覆蓋點相對於圓心的角度
    angles = []
    for point in covered_points:
        dx = point[0] - cx
        dy = point[1] - cy
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        angles.append(angle)
    
    angles.sort()
    
    # 找出最大角度範圍
    if len(angles) == 1:
        # 只有一個點，使用小弧段
        start_angle = angles[0] - 30
        end_angle = angles[0] + 30
    else:
        # 找出覆蓋所有點的最小弧段
        start_angle = min(angles) - 10  # 留一些邊距
        end_angle = max(angles) + 10
    
    # 正規化角度
    start_angle = start_angle % 360
    end_angle = end_angle % 360
    
    # 計算弧長
    if end_angle > start_angle:
        arc_angle = end_angle - start_angle
    else:
        arc_angle = 360 - start_angle + end_angle
    
    arc_length = (arc_angle / 360) * 2 * math.pi * radius
    
    return {
        'arc_length': float(arc_length),
        'start_angle': float(start_angle),
        'end_angle': float(end_angle)
    }


def optimize_3_circles(points):
    """
    優化3心圓配置
    
    Args:
        points: 8個控制點座標
    
    Returns:
        dict: 優化結果
    """
    return optimize_circles(points, 3)


def optimize_4_circles(points):
    """
    優化4心圓配置
    
    Args:
        points: 8個控制點座標
    
    Returns:
        dict: 優化結果
    """
    return optimize_circles(points, 4)
