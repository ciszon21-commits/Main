"""
類型二：特定水深下的輸送容量
Type 2: Transport capacity at specific depth
"""

from .manning_calculator import calculate_flow_rate, calculate_velocity

def calculate_capacity_at_depth(roughness, diameter, slope, depth_ratio):
    """
    計算特定水深比下的流速及流量
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        slope: 坡度 S (m/m)
        depth_ratio: 水深比 d/D
    
    Returns:
        Dictionary with velocity and flow_rate (CMD)
    """
    flow_rate_m3s = calculate_flow_rate(roughness, diameter, slope, depth_ratio)
    velocity = calculate_velocity(roughness, diameter, slope, depth_ratio)
    
    # 轉換流量單位：m³/s -> CMD
    flow_rate_cmd = flow_rate_m3s * 86400
    
    return {
        'depth_ratio': depth_ratio,
        'velocity': round(velocity, 2),
        'flow_rate': int(round(flow_rate_cmd))
    }
