"""
類型五：維持流速之坡降
Type 5: Slope for maintaining velocity at specific flow
"""

from .manning_calculator import calculate_slope_for_velocity, calculate_depth_ratio_for_flow
from .hydraulic_geometry import generate_depth_ratios

def calculate_slope_for_velocity_and_flow(roughness, diameter, target_velocity, target_flow_cmd):
    """
    計算維持目標流速和流量所需的坡度（各水深比）
    
    Args:
        roughness: 粗糙係數 n
        diameter: 管徑 D (m)
        target_velocity: 目標流速 V (m/s)
        target_flow_cmd: 目標流量 (CMD)
    
    Returns:
        Dictionary with results table and recommended depth_ratio
    """
    results = []
    depth_ratios = generate_depth_ratios(0.05, 1.0, 0.05)
    
    # 將 CMD 轉換為 m³/s
    target_flow_m3s = target_flow_cmd / 86400
    
    # 從流量反推可能的水深比
    # 使用迭代法找出各個坡度下能達到目標流量的水深比
    for dr in depth_ratios:
        slope = calculate_slope_for_velocity(roughness, diameter, target_velocity, dr)
        
        # 檢查此坡度和水深比下的流量
        from .manning_calculator import calculate_flow_rate
        actual_flow_m3s = calculate_flow_rate(roughness, diameter, slope, dr)
        actual_flow_cmd = actual_flow_m3s * 86400
        
        # 計算流量誤差
        flow_error = abs(actual_flow_cmd - target_flow_cmd)
        flow_error_percent = (flow_error / target_flow_cmd * 100) if target_flow_cmd > 0 else 0
        
        results.append({
            'depth_ratio': dr,
            'slope': round(slope, 6),
            'actual_flow': int(round(actual_flow_cmd)),
            'flow_error_percent': round(flow_error_percent, 2)
        })
    
    # 找出流量誤差最小的水深比
    min_error_result = min(results, key=lambda x: x['flow_error_percent'])
    
    return {
        'table': results,
        'recommended_depth_ratio': min_error_result['depth_ratio'],
        'recommended_slope': min_error_result['slope']
    }
