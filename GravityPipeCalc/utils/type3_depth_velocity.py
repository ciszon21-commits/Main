"""
類型三：水深與流速
Type 3: Depth and velocity
"""

from .manning_calculator import calculate_velocity, calculate_depth_ratio_for_flow
from .hydraulic_geometry import generate_depth_ratios

def calculate_depth_velocity_table(roughness, diameter, slope, flow_rate_cmd):
    """
    計算給定流量下，各水深比的流速
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        slope: 坡度 S (m/m)
        flow_rate_cmd: 流量 (CMD)
    
    Returns:
        List of dictionaries with depth_ratio and velocity
    """
    results = []
    depth_ratios = generate_depth_ratios(0.05, 1.0, 0.05)
    
    # 將 CMD 轉換為 m³/s
    flow_rate_m3s = flow_rate_cmd / 86400
    
    # 先找出能達到目標流量的水深比
    target_depth_ratio = calculate_depth_ratio_for_flow(
        roughness, diameter, slope, flow_rate_m3s
    )
    
    for dr in depth_ratios:
        velocity = calculate_velocity(roughness, diameter, slope, dr)
        
        # 標記是否為目標流量對應的水深比
        is_target = False
        if target_depth_ratio and abs(dr - target_depth_ratio) < 0.025:
            is_target = True
        
        results.append({
            'depth_ratio': dr,
            'velocity': round(velocity, 2),  # 取到小數點兩位
            'is_target': is_target
        })
    
    return {
        'table': results,
        'target_depth_ratio': round(target_depth_ratio, 3) if target_depth_ratio else None
    }
