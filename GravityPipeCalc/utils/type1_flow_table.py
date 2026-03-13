"""
類型一：管線輸送流量表
Type 1: Pipeline flow rate table
"""

from .manning_calculator import calculate_flow_rate, calculate_velocity
from .hydraulic_geometry import generate_depth_ratios

def calculate_flow_table(roughness, diameter, slope):
    """
    計算管線在各水深比下的流量、流速
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        slope: 坡度 S (m/m)
    
    Returns:
        List of dictionaries with depth_ratio, flow_rate (CMD), velocity
    """
    results = []
    depth_ratios = generate_depth_ratios(0.05, 1.0, 0.05)
    
    for dr in depth_ratios:
        flow_rate_m3s = calculate_flow_rate(roughness, diameter, slope, dr)
        velocity = calculate_velocity(roughness, diameter, slope, dr)
        
        # 轉換流量單位：m³/s -> CMD (立方公尺/日)
        flow_rate_cmd = flow_rate_m3s * 86400
        
        results.append({
            'depth_ratio': dr,
            'flow_rate': int(round(flow_rate_cmd)),  # 取整到整數位
            'velocity': round(velocity, 2)  # 取到小數點兩位
        })
    
    return results
