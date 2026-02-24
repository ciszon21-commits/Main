"""
類型七：輸送流量之坡降
Type 7: Slope for transporting flow at specific depth
"""

from .manning_calculator import calculate_slope_for_flow, calculate_velocity

def calculate_slope_for_flow_and_depth(roughness, diameter, target_flow_cmd, depth_ratio):
    """
    計算特定水深比下輸送目標流量所需的坡度及流速
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        target_flow_cmd: 目標流量 (CMD)
        depth_ratio: 水深比 d/D
    
    Returns:
        Dictionary with slope and velocity
    """
    # 將 CMD 轉換為 m³/s
    target_flow_m3s = target_flow_cmd / 86400
    
    slope = calculate_slope_for_flow(roughness, diameter, target_flow_m3s, depth_ratio)
    velocity = calculate_velocity(roughness, diameter, slope, depth_ratio)
    
    return {
        'depth_ratio': depth_ratio,
        'slope': round(slope, 6),
        'velocity': round(velocity, 2)  # 取到小數點兩位
    }
