"""
類型四：維持流速之坡降表
Type 4: Slope table for maintaining velocity
"""

from .manning_calculator import calculate_slope_for_velocity, calculate_flow_rate
from .hydraulic_geometry import generate_depth_ratios

def calculate_slope_table_for_velocity(roughness, diameter, target_velocity):
    """
    計算維持目標流速所需的坡度表（各水深比）
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        target_velocity: 目標流速 V (m/s)
    
    Returns:
        List of dictionaries with depth_ratio, slope, and flow_rate (CMD)
    """
    results = []
    depth_ratios = generate_depth_ratios(0.05, 1.0, 0.05)
    
    for dr in depth_ratios:
        slope = calculate_slope_for_velocity(roughness, diameter, target_velocity, dr)
        flow_rate_m3s = calculate_flow_rate(roughness, diameter, slope, dr)
        
        # 轉換流量單位：m³/s -> CMD
        flow_rate_cmd = flow_rate_m3s * 86400
        
        results.append({
            'depth_ratio': dr,
            'slope': round(slope, 6),
            'flow_rate': int(round(flow_rate_cmd))
        })
    
    return results
