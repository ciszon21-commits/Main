"""
計算與兩個圓相切的第三個圓的幾何算法
"""
import math
import numpy as np


def calculate_tangent_circle(c1_x, c1_y, r1, c2_x, c2_y, r2, points, mode='external'):
    """
    計算與兩個圓相切的第三個圓
    
    Args:
        c1_x, c1_y, r1: 第一個圓的圓心和半徑
        c2_x, c2_y, r2: 第二個圓的圓心和半徑
        points: 控制點陣列（用於驗證覆蓋）
        mode: 'external' (外切) 或 'internal' (內切)
    
    Returns:
        dict: 包含第三個圓的參數 {center_x, center_y, radius}
    """
    # 計算兩圓圓心距離
    d = math.sqrt((c2_x - c1_x)**2 + (c2_y - c1_y)**2)
    
    # 如果兩圓太近或重疊，返回預設值
    if d < abs(r1 - r2) + 0.1:
        # 使用簡單的預設第三個圓
        mid_x = (c1_x + c2_x) / 2
        mid_y = max(c1_y, c2_y) + max(r1, r2)
        default_r = max(r1, r2) * 0.8
        return {
            'center_x': mid_x,
            'center_y': mid_y,
            'radius': default_r
        }
    
    # 嘗試多種方案找到最佳的第三個圓
    best_circle = None
    best_coverage = 0
    
    # 方案1: 在兩圓上方的外切圓
    for r3_multiplier in [1.0, 1.2, 1.5, 2.0, 2.5]:
        r3 = max(r1, r2) * r3_multiplier
        
        # 使用Apollonius問題的解法
        # 對於外切情況，第三個圓與兩個圓都外切
        # 圓心距離關係：d13 = r1 + r3, d23 = r2 + r3
        
        # 設第三個圓心為 (x3, y3)
        # (x3 - c1_x)^2 + (y3 - c1_y)^2 = (r1 + r3)^2
        # (x3 - c2_x)^2 + (y3 - c2_y)^2 = (r2 + r3)^2
        
        # 求解這個方程組
        a = c2_x - c1_x
        b = c2_y - c1_y
        c = ((r1 + r3)**2 - (r2 + r3)**2 - c1_x**2 + c2_x**2 - c1_y**2 + c2_y**2) / 2
        
        if abs(b) > 0.001:
            # y3 = (c - a*x3) / b
            # 代入第一個圓的方程求解 x3
            A = 1 + (a/b)**2
            B = 2*(-c1_x - (a/b)*(c/b - c1_y))
            C = c1_x**2 + (c/b - c1_y)**2 - (r1 + r3)**2
            
            discriminant = B**2 - 4*A*C
            if discriminant >= 0:
                x3_1 = (-B + math.sqrt(discriminant)) / (2*A)
                x3_2 = (-B - math.sqrt(discriminant)) / (2*A)
                
                for x3 in [x3_1, x3_2]:
                    y3 = (c - a*x3) / b
                    
                    # 驗證這個圓是否覆蓋足夠多的點
                    coverage = count_covered_points(points, [(c1_x, c1_y, r1), (c2_x, c2_y, r2), (x3, y3, r3)])
                    
                    if coverage > best_coverage:
                        best_coverage = coverage
                        best_circle = {'center_x': x3, 'center_y': y3, 'radius': r3}
        else:
            # b ≈ 0, 特殊情況
            if abs(a) > 0.001:
                x3 = c / a
                # 代入第一個圓的方程求解 y3
                y3_squared = (r1 + r3)**2 - (x3 - c1_x)**2
                if y3_squared >= 0:
                    y3_1 = c1_y + math.sqrt(y3_squared)
                    y3_2 = c1_y - math.sqrt(y3_squared)
                    
                    for y3 in [y3_1, y3_2]:
                        coverage = count_covered_points(points, [(c1_x, c1_y, r1), (c2_x, c2_y, r2), (x3, y3, r3)])
                        
                        if coverage > best_coverage:
                            best_coverage = coverage
                            best_circle = {'center_x': x3, 'center_y': y3, 'radius': r3}
    
    # 如果找不到較好的解，使用簡單的預設方案
    if best_circle is None or best_coverage < len(points):
        # 計算能覆蓋所有未被前兩圓覆蓋的點的最小圓
        uncovered_points = []
        for point in points:
            if not (point_in_circle(point, c1_x, c1_y, r1) or point_in_circle(point, c2_x, c2_y, r2)):
                uncovered_points.append(point)
        
        if uncovered_points:
            # 計算最小包圍圓
            uc_array = np.array(uncovered_points)
            center_x = np.mean(uc_array[:, 0])
            center_y = np.mean(uc_array[:, 1])
            
            # 計算需要的半徑
            max_dist = 0
            for point in uncovered_points:
                dist = math.sqrt((point[0] - center_x)**2 + (point[1] - center_y)**2)
                max_dist = max(max_dist, dist)
            
            radius = max_dist + 1  # 加一點邊距
            
            best_circle = {
                'center_x': float(center_x),
                'center_y': float(center_y),
                'radius': float(radius)
            }
        else:
            # 所有點都被覆蓋，返回一個小的裝飾性圓
            mid_x = (c1_x + c2_x) / 2
            mid_y = max(c1_y, c2_y) + (r1 + r2) / 2
            best_circle = {
                'center_x': mid_x,
                'center_y': mid_y,
                'radius': min(r1, r2) * 0.5
            }
    
    return best_circle


def point_in_circle(point, cx, cy, r):
    """檢查點是否在圓內"""
    dist = math.sqrt((point[0] - cx)**2 + (point[1] - cy)**2)
    return dist <= r + 0.1


def count_covered_points(points, circles):
    """計算被圓覆蓋的點數量"""
    count = 0
    for point in points:
        for cx, cy, r in circles:
            if point_in_circle(point, cx, cy, r):
                count += 1
                break
    return count


def calculate_intersection_of_normals(c1_x, c1_y, angle1, c2_x, c2_y, angle2):
    """
    計算兩條法線（由圓心和角度定義）的交點
    Normal 1: (c1_x, c1_y) -> angle1
    Normal 2: (c2_x, c2_y) -> angle2
    """
    # Line 1: x = c1_x + t * cos(a1), y = c1_y + t * sin(a1)
    # y - c1_y = tan(a1) * (x - c1_x)
    
    rad1 = math.radians(angle1)
    rad2 = math.radians(angle2)
    
    # 處理垂直線情況 (tan 無限大)
    EPS = 1e-9
    
    def get_line_params(cx, cy, rad):
        cos_v = math.cos(rad)
        sin_v = math.sin(rad)
        if abs(cos_v) < EPS: return (1, 0, cx) # x = cx
        m = sin_v / cos_v
        # y - cy = m(x - cx) => -mx + y = -m*cx + cy
        return (-m, 1, -m*cx + cy)

    a1, b1, k1 = get_line_params(c1_x, c1_y, rad1)
    a2, b2, k2 = get_line_params(c2_x, c2_y, rad2)
    
    det = a1 * b2 - a2 * b1
    
    if abs(det) < EPS:
        return None # 平行線
        
    x = (b2 * k1 - b1 * k2) / det
    y = (a1 * k2 - a2 * k1) / det
    return {'x': x, 'y': y}

def optimize_4_circles_interactive(c1_x, c1_y, r1, c2_x, c2_y, r2, points, c1_angles=None, c2_angles=None):
    """
    互動模式求解 4心圓
    C1, C2 由用戶定義 (包含角度範圍)
    C3 (左側), C4 (右側) 自動求解以連接 C1, C2
    """
    circles_data = []
    
    # 確保角度存在
    if not c1_angles: c1_angles = (0, 120)
    if not c2_angles: c2_angles = (240, 360)
    
    start1, end1 = c1_angles
    start2, end2 = c2_angles
    
    # --- 1. 定義 C1, C2 ---
    circle1 = {
        'circle_index': 0, 
        'center_x': c1_x, 'center_y': c1_y, 'radius': r1,
        'start_angle': start1, 'end_angle': end1
    }
    circle2 = {
        'circle_index': 1,
        'center_x': c2_x, 'center_y': c2_y, 'radius': r2,
        'start_angle': start2, 'end_angle': end2
    }
    
    # --- 2. 求解 C3 (Arc 1 End -> Arc 2 Start) ---
    # User Gap: End1 -> Start2
    # Normal 1 define by End1
    # Normal 2 define by Start2
    inter3 = calculate_intersection_of_normals(c1_x, c1_y, end1, c2_x, c2_y, start2)
    
    circle3 = None
    if inter3:
        # 計算到兩個切點的距離
        # 切點 P1: C1圓周上角度為 End1 的點
        p1x = c1_x + r1 * math.cos(math.radians(end1))
        p1y = c1_y + r1 * math.sin(math.radians(end1))
        
        p2x = c2_x + r2 * math.cos(math.radians(start2))
        p2y = c2_y + r2 * math.sin(math.radians(start2))
        
        d1 = math.sqrt((inter3['x'] - p1x)**2 + (inter3['y'] - p1y)**2)
        d2 = math.sqrt((inter3['x'] - p2x)**2 + (inter3['y'] - p2y)**2)
        
        # 半徑取平均
        r3 = (d1 + d2) / 2
        
        # 定義圓3
        # 角度範圍：從 P2(Start2) 的反向延伸到 P1(End1) 的反向延伸？
        # C3 連接 P1 和 P2。
        # Angle from C3 to P1 (End of Arc 3)
        # Angle from C3 to P2 (Start of Arc 3)
        # 注意方向：Arc 3 連接 Arc 1 End -> Arc 2 Start.
        # 所以 Arc 3 Start 是 P1 (End1), Arc 3 End 是 P2 (Start2).
        
        ang3_start = math.degrees(math.atan2(p1y - inter3['y'], p1x - inter3['x']))
        ang3_end = math.degrees(math.atan2(p2y - inter3['y'], p2x - inter3['x']))
        
        circle3 = {
            'circle_index': 2,
            'center_x': inter3['x'],
            'center_y': inter3['y'],
            'radius': r3,
            'start_angle': ang3_start,
            'end_angle': ang3_end
        }
        
    # --- 3. 求解 C4 (Arc 2 End -> Arc 1 Start) ---
    # User Gap: End2 -> Start1
    inter4 = calculate_intersection_of_normals(c2_x, c2_y, end2, c1_x, c1_y, start1)
    
    circle4 = None
    if inter4:
        p2x = c2_x + r2 * math.cos(math.radians(end2))
        p2y = c2_y + r2 * math.sin(math.radians(end2))
        
        p1x = c1_x + r1 * math.cos(math.radians(start1))
        p1y = c1_y + r1 * math.sin(math.radians(start1))
        
        d1 = math.sqrt((inter4['x'] - p2x)**2 + (inter4['y'] - p2y)**2)
        d2 = math.sqrt((inter4['x'] - p1x)**2 + (inter4['y'] - p1y)**2)
        
        r4 = (d1 + d2) / 2
        
        ang4_start = math.degrees(math.atan2(p2y - inter4['y'], p2x - inter4['x']))
        ang4_end = math.degrees(math.atan2(p1y - inter4['y'], p1x - inter4['x']))
        
        circle4 = {
            'circle_index': 3,
            'center_x': inter4['x'],
            'center_y': inter4['y'],
            'radius': r4,
            'start_angle': ang4_start,
            'end_angle': ang4_end
        }

    # 計算弧長與正規化角度
    result_circles = []
    for c in [circle1, circle2, circle3, circle4]:
        if c:
            # 正規化角度
            s, e = c['start_angle'], c['end_angle']
            # 確保正向跨越
            diff = e - s
            while diff < 0: diff += 360
            while diff >= 360: diff -= 360
            
            # 不修改 C1, C2 的原始輸入角度 (User defined)
            # 但計算 arc_length
            arc_length = (diff / 360) * 2 * math.pi * c['radius']
            
            c.update({
                'start_angle': float(s),
                'end_angle': float(e),
                'arc_length': float(arc_length)
            })
            result_circles.append(c)
            
    total_area = sum([math.pi * c['radius']**2 for c in result_circles])
    
    return {
        'success': True,
        'circles': result_circles,
        'total_area': float(total_area),
        'message': 'Interactive 4-circle configuration'
    }
