"""
曼寧公式計算器
Manning equation calculator for gravity pipe flow
"""

import math
from .hydraulic_geometry import (
    calculate_flow_area,
    calculate_hydraulic_radius,
    calculate_wetted_perimeter
)

def calculate_flow_rate(roughness, diameter, slope, depth_ratio):
    """
    使用曼寧公式計算流量
    Calculate flow rate using Manning equation
    
    Q = (1/n) * A * R^(2/3) * S^(1/2)
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        slope: 坡度 S (m/m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Flow rate Q (m³/s)
    """
    if depth_ratio <= 0 or slope <= 0:
        return 0
    
    area = calculate_flow_area(diameter, depth_ratio)
    hydraulic_radius = calculate_hydraulic_radius(diameter, depth_ratio)
    
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    flow_rate = (1 / roughness) * area * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
    return flow_rate

def calculate_velocity(roughness, diameter, slope, depth_ratio):
    """
    計算流速
    Calculate velocity
    
    V = Q / A = (1/n) * R^(2/3) * S^(1/2)
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        slope: 坡度 S (m/m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Velocity V (m/s)
    """
    if depth_ratio <= 0 or slope <= 0:
        return 0
    
    hydraulic_radius = calculate_hydraulic_radius(diameter, depth_ratio)
    
    # V = (1/n) * R^(2/3) * S^(1/2)
    velocity = (1 / roughness) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
    return velocity

def calculate_depth_ratio_for_flow(roughness, diameter, slope, target_flow, 
                                   tolerance=0.001, max_iterations=100):
    """
    使用迭代法計算達到目標流量所需的水深比
    Calculate depth ratio for target flow rate using iterative method
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        slope: 坡度 S (m/m)
        target_flow: 目標流量 Q (m³/s)
        tolerance: 容許誤差
        max_iterations: 最大迭代次數
    
    Returns:
        Depth ratio d/D or None if not converged
    """
    # 使用二分法求解
    low = 0.01
    high = 1.0
    
    for _ in range(max_iterations):
        mid = (low + high) / 2
        calculated_flow = calculate_flow_rate(roughness, diameter, slope, mid)
        
        if abs(calculated_flow - target_flow) < tolerance:
            return mid
        
        if calculated_flow < target_flow:
            low = mid
        else:
            high = mid
    
    return None  # 未收斂

def calculate_slope_for_velocity(roughness, diameter, target_velocity, depth_ratio):
    """
    計算達到目標流速所需的坡度
    Calculate slope for target velocity
    
    S = (V * n / R^(2/3))²
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        target_velocity: 目標流速 V (m/s)
        depth_ratio: 水深比 d/D
    
    Returns:
        Slope S (m/m)
    """
    if depth_ratio <= 0 or target_velocity <= 0:
        return 0
    
    hydraulic_radius = calculate_hydraulic_radius(diameter, depth_ratio)
    
    if hydraulic_radius <= 0:
        return 0
    
    # S = (V * n / R^(2/3))²
    slope = (target_velocity * roughness / (hydraulic_radius ** (2/3))) ** 2
    return slope

def calculate_slope_for_flow(roughness, diameter, target_flow, depth_ratio):
    """
    計算達到目標流量所需的坡度
    Calculate slope for target flow rate
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        target_flow: 目標流量 Q (m³/s)
        depth_ratio: 水深比 d/D
    
    Returns:
        Slope S (m/m)
    """
    if depth_ratio <= 0 or target_flow <= 0:
        return 0
    
    area = calculate_flow_area(diameter, depth_ratio)
    hydraulic_radius = calculate_hydraulic_radius(diameter, depth_ratio)
    
    if area <= 0 or hydraulic_radius <= 0:
        return 0
    
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    # S = (Q * n / (A * R^(2/3)))²
    slope = (target_flow * roughness / (area * (hydraulic_radius ** (2/3)))) ** 2
    return slope

def calculate_diameter_for_conditions(roughness, target_velocity, target_flow, 
                                      depth_ratio, tolerance=0.001):
    """
    計算滿足流速、流量和水深比條件的管徑
    Calculate diameter for given velocity, flow rate, and depth ratio
    
    Args:
        roughness: 粗糙係數 n
        target_velocity: 目標流速 V (m/s)
        target_flow: 目標流量 Q (m³/s)
        depth_ratio: 水深比 d/D
        tolerance: 容許誤差
    
    Returns:
        Tuple of (diameter, slope) or (None, None) if not found
    """
    # 從 Q = V * A 推導管徑
    # A = Q / V
    required_area = target_flow / target_velocity
    
    # 使用迭代法求解管徑
    low = 0.1
    high = 10.0
    
    for _ in range(100):
        mid_diameter = (low + high) / 2
        area = calculate_flow_area(mid_diameter, depth_ratio)
        
        if abs(area - required_area) < tolerance:
            # 找到管徑後，計算所需坡度
            slope = calculate_slope_for_velocity(roughness, mid_diameter, 
                                                 target_velocity, depth_ratio)
            return mid_diameter, slope
        
        if area < required_area:
            low = mid_diameter
        else:
            high = mid_diameter
    
    return None, None
