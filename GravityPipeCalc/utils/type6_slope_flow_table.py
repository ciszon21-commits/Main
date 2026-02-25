"""
類型六：輸送流量之坡降表
Type 6: Slope table for transporting flow
"""

from .manning_calculator import calculate_slope_for_flow, calculate_velocity
from .hydraulic_geometry import generate_depth_ratios

def calculate_slope_table_for_flow(roughness, diameter, target_flow_cmd):
    """
    計算輸送目標流量所需的坡度表（各水深比）
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        target_flow_cmd: 目標流量 (CMD)
    
    Returns:
        List of dictionaries with depth_ratio, slope, and velocity
    """
    results = []
    depth_ratios = generate_depth_ratios(0.05, 1.0, 0.05)
    
    # 將 CMD 轉換為 m³/s
    target_flow_m3s = target_flow_cmd / 86400
    
    for dr in depth_ratios:
        slope = calculate_slope_for_flow(roughness, diameter, target_flow_m3s, dr)
        velocity = calculate_velocity(roughness, diameter, slope, dr)
        
        results.append({
            'depth_ratio': dr,
            'slope': round(slope, 6),
            'velocity': round(velocity, 2)  # 取到小數點兩位
        })
    
    return results
