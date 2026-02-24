"""
類型八：維持流速、流量及特定水深比下的建議管徑
Type 8: Recommended diameter for maintaining velocity, flow, and specific depth ratio
"""

from .manning_calculator import calculate_diameter_for_conditions

def calculate_recommended_diameter(roughness, target_velocity, target_flow_cmd, depth_ratio):
    """
    計算滿足流速、流量和水深比條件的建議管徑及坡度
    
    Args:
        roughness: 粗糙係數 n
        target_velocity: 目標流速 V (m/s)
        target_flow_cmd: 目標流量 (CMD)
        depth_ratio: 水深比 d/D
    
    Returns:
        Dictionary with recommended diameter (mm) and slope
    """
    # 將 CMD 轉換為 m³/s
    target_flow_m3s = target_flow_cmd / 86400
    
    diameter_m, slope = calculate_diameter_for_conditions(
        roughness, target_velocity, target_flow_m3s, depth_ratio
    )
    
    if diameter_m is None:
        return {
            'success': False,
            'message': '無法找到滿足條件的管徑，請檢查輸入參數是否合理'
        }
    
    # 轉換管徑為 mm
    diameter_mm = diameter_m * 1000
    
    # 提供標準管徑建議（mm）- 向上取整到常見規格
    standard_diameters_mm = [200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 
                             900, 1000, 1200, 1350, 1500, 1650, 1800, 2000, 2200, 2400, 
                             2600, 2800, 3000, 3500, 4000]
    
    recommended_standard = None
    for std_d in standard_diameters_mm:
        if std_d >= diameter_mm:
            recommended_standard = std_d
            break
    
    if recommended_standard is None:
        recommended_standard = standard_diameters_mm[-1]
    
    return {
        'success': True,
        'calculated_diameter': int(round(diameter_mm)),  # mm，取整數
        'recommended_standard_diameter': recommended_standard,  # mm
        'slope': round(slope, 6),
        'depth_ratio': depth_ratio,
        'velocity': target_velocity,
        'flow_rate': target_flow_cmd  # 返回 CMD 單位
    }
