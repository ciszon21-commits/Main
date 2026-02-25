"""
圓形管道水理幾何計算
Hydraulic geometry calculations for circular pipes
"""

import math

def calculate_theta(depth_ratio):
    """
    計算圓心角 θ (弧度)
    Calculate central angle θ in radians
    
    Args:
        depth_ratio: 水深比 d/D (depth ratio)
    
    Returns:
        θ in radians
    """
    if depth_ratio <= 0:
        return 0
    if depth_ratio >= 1:
        return 2 * math.pi
    
    # θ = 2 * arccos(1 - 2 * d/D)
    theta = 2 * math.acos(1 - 2 * depth_ratio)
    return theta

def calculate_flow_area(diameter, depth_ratio):
    """
    計算流動面積 A
    Calculate flow area
    
    Args:
        diameter: 管徑 D (m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Flow area A (m²)
    """
    if depth_ratio <= 0:
        return 0
    if depth_ratio >= 1:
        return math.pi * (diameter / 2) ** 2
    
    theta = calculate_theta(depth_ratio)
    radius = diameter / 2
    
    # A = (r² / 2) * (θ - sin(θ))
    area = (radius ** 2 / 2) * (theta - math.sin(theta))
    return area

def calculate_wetted_perimeter(diameter, depth_ratio):
    """
    計算濕周 P
    Calculate wetted perimeter
    
    Args:
        diameter: 管徑 D (m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Wetted perimeter P (m)
    """
    if depth_ratio <= 0:
        return 0
    if depth_ratio >= 1:
        return math.pi * diameter
    
    theta = calculate_theta(depth_ratio)
    radius = diameter / 2
    
    # P = r * θ
    perimeter = radius * theta
    return perimeter

def calculate_hydraulic_radius(diameter, depth_ratio):
    """
    計算水力半徑 R
    Calculate hydraulic radius
    
    Args:
        diameter: 管徑 D (m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Hydraulic radius R (m)
    """
    if depth_ratio <= 0:
        return 0
    
    area = calculate_flow_area(diameter, depth_ratio)
    perimeter = calculate_wetted_perimeter(diameter, depth_ratio)
    
    if perimeter == 0:
        return 0
    
    # R = A / P
    return area / perimeter

def calculate_top_width(diameter, depth_ratio):
    """
    計算水面寬度 T
    Calculate top width
    
    Args:
        diameter: 管徑 D (m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Top width T (m)
    """
    if depth_ratio <= 0 or depth_ratio >= 1:
        return 0
    
    depth = depth_ratio * diameter
    radius = diameter / 2
    
    # T = 2 * sqrt(r² - (r - d)²)
    top_width = 2 * math.sqrt(radius ** 2 - (radius - depth) ** 2)
    return top_width

def generate_depth_ratios(start=0.05, end=1.0, step=0.05):
    """
    生成水深比序列
    Generate depth ratio sequence
    
    Args:
        start: 起始值
        end: 結束值
        step: 步長
    
    Returns:
        List of depth ratios
    """
    ratios = []
    current = start
    while current <= end + 1e-9:  # 加入小誤差容忍
        ratios.append(round(current, 2))
        current += step
    return ratios
