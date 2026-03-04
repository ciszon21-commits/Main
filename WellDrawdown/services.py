"""
水理分析抽水預測系統 — Theis & Neuman 計算核心
"""
import io
import base64
import math

import numpy as np
from scipy.special import exp1  # E1(u) — Theis 井函數
from scipy.integrate import quad
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize


# ─────────────────────────────────────────────
# Theis 方法
# ─────────────────────────────────────────────
def theis_well_function(u):
    """W(u) = E1(u)  (指數積分)"""
    return exp1(u)


def theis_drawdown(Q, T, S, r, t):
    """
    Theis 法：計算單井在距離 r、時間 t 的洩降量 s
    s = Q / (4πT) * W(u)
    u = r²S / (4Tt)
    """
    if r <= 0 or t <= 0:
        return 0.0
    u = (r ** 2 * S) / (4.0 * T * t)
    if u > 500:
        return 0.0
    W = float(theis_well_function(u))
    s = Q / (4.0 * math.pi * T) * W
    return s


# ─────────────────────────────────────────────
# Neuman 方法 (無圍壓含水層)
# ─────────────────────────────────────────────
def neuman_drawdown(Q, T, S, Sy, Kh, Kv, b, r, t):
    """
    Neuman 法洩降公式 (簡化數值積分版)

    使用 Neuman (1975) 的無圍壓含水層井函數。
    參數:
        Q   - 抽水量 (m³/day)
        T   - 導水係數 (m²/day)
        S   - 貯水係數 (-)
        Sy  - 比出水量 (-)
        Kh  - 水平滲透係數 (m/day)
        Kv  - 垂直滲透係數 (m/day)
        b   - 含水層厚度 (m)
        r   - 距離 (m)
        t   - 抽水時間 (day)
    """
    if r <= 0 or t <= 0:
        return 0.0

    # 無因次參數
    ts = T * t / (S * r ** 2)       # 早期無因次時間
    ty = T * t / (Sy * r ** 2)      # 晚期無因次時間
    beta = (Kv / Kh) * (r / b) ** 2  # 各向異性參數

    # Neuman 井函數的數值近似
    # 早期 (受壓行為) — 與 Theis 類似
    u_early = 1.0 / (4.0 * ts) if ts > 0 else 1e10
    if u_early > 500:
        W_early = 0.0
    else:
        W_early = float(exp1(u_early))

    # 晚期 (洩水行為) — 與 Theis(Sy) 類似
    u_late = 1.0 / (4.0 * ty) if ty > 0 else 1e10
    if u_late > 500:
        W_late = 0.0
    else:
        W_late = float(exp1(u_late))

    # 過渡期修正係數 — Neuman 的 β 修正
    transition = 1.0 - math.exp(-beta * ty) if beta * ty < 500 else 1.0

    # 組合：早期+過渡→晚期
    W_neuman = W_early * (1.0 - transition) + W_late * transition

    s = Q / (4.0 * math.pi * T) * W_neuman
    return s


# ─────────────────────────────────────────────
# 多井疊加
# ─────────────────────────────────────────────
def distance(p1, p2):
    """兩點距離"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def total_drawdown_at_point(point, wells, Q_list, params, method='theis'):
    """
    計算某點受所有井疊加的總洩降。
    wells: [(x, y), ...]
    Q_list: [Q1, Q2, ...] (m³/day)
    params: dict with T, S, t, (Sy, Kh, Kv, b for neuman)
    """
    s_total = 0.0
    for i, well in enumerate(wells):
        r = distance(point, well)
        if r < 0.1:
            r = 0.1  # 避免 r=0 奇異值
        Q = Q_list[i]
        if method == 'theis':
            s_total += theis_drawdown(Q, params['T'], params['S'], r, params['t'])
        else:
            s_total += neuman_drawdown(
                Q, params['T'], params['S'],
                params['Sy'], params['Kh'], params['Kv'],
                params['b'], r, params['t']
            )
    return s_total


# ─────────────────────────────────────────────
# 多邊形內部判定 (射線法)
# ─────────────────────────────────────────────
def point_in_polygon(point, polygon):
    """
    射線法 (Ray Casting) 判定點是否在多邊形內部。
    polygon: [(x, y), ...]
    """
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


# ─────────────────────────────────────────────
# 反推各井抽水量
# ─────────────────────────────────────────────
def _generate_check_points(station_coords, n_per_edge=5, grid_spacing=5.0):
    """
    在車站外框多邊形的「邊界 + 內部」產生檢核點。
    1) 邊界上的等分點 (含頂點)
    2) 在 bounding box 內產生均勻格點，過濾出多邊形內的點
    """
    check_points = []

    # 邊界檢核點
    n = len(station_coords)
    for i in range(n):
        p1 = station_coords[i]
        p2 = station_coords[(i + 1) % n]
        for j in range(n_per_edge):
            ratio = j / n_per_edge
            x = p1[0] + ratio * (p2[0] - p1[0])
            y = p1[1] + ratio * (p2[1] - p1[1])
            check_points.append((x, y))

    # 內部格點檢核 — 在 bounding box 中布點，過濾在多邊形內的
    xs = [p[0] for p in station_coords]
    ys = [p[1] for p in station_coords]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    x_pts = np.arange(x_min + grid_spacing, x_max, grid_spacing)
    y_pts = np.arange(y_min + grid_spacing, y_max, grid_spacing)

    for xp in x_pts:
        for yp in y_pts:
            if point_in_polygon((xp, yp), station_coords):
                check_points.append((xp, yp))

    return check_points


def compute_required_Q(wells, station_coords, params, method='theis', target_drawdown=None):
    """
    反推各井所需抽水量，使車站外框線內所有檢核點的洩降 >= 目標深度。

    returns: list of Q values (m³/day)
    """
    if target_drawdown is None:
        target_drawdown = params.get('excavation_depth', 10.0)

    n_wells = len(wells)
    check_points = _generate_check_points(station_coords)

    def objective(Q_array):
        """最小化目標：各檢核點洩降與目標深度差的平方和 (重懲罰不足)"""
        total_error = 0.0
        for pt in check_points:
            s = total_drawdown_at_point(pt, wells, Q_array, params, method)
            deficit = target_drawdown - s
            if deficit > 0:
                # 車站內部洩降不足 → 重懲罰
                total_error += (deficit ** 2) * 50.0
            else:
                # 洩降已超過目標 → 輕懲罰 (避免過度抽水)
                total_error += (deficit ** 2) * 0.05
        # 總抽水量正則化
        total_error += 0.0005 * np.sum(Q_array ** 2)
        return total_error

    # 初始猜測
    Q0 = np.full(n_wells, 5000.0)
    bounds = [(100.0, 50000.0)] * n_wells

    result = minimize(objective, Q0, method='L-BFGS-B', bounds=bounds,
                      options={'maxiter': 3000, 'ftol': 1e-12})

    return result.x.tolist()


# ─────────────────────────────────────────────
# Contour 圖生成 (深色主題)
# ─────────────────────────────────────────────
def generate_contour(wells, Q_list, station_coords, params, method='theis'):
    """
    產生 drawdown contour 圖 (深色主題)，回傳 base64 PNG。
    """
    # 計算繪圖範圍
    all_x = [w[0] for w in wells] + [s[0] for s in station_coords]
    all_y = [w[1] for w in wells] + [s[1] for s in station_coords]
    margin = 50
    x_min, x_max = min(all_x) - margin, max(all_x) + margin
    y_min, y_max = min(all_y) - margin, max(all_y) + margin

    # 產生格點
    nx, ny = 200, 200
    x_grid = np.linspace(x_min, x_max, nx)
    y_grid = np.linspace(y_min, y_max, ny)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = np.zeros_like(X)

    for i in range(ny):
        for j in range(nx):
            pt = (X[i, j], Y[i, j])
            Z[i, j] = total_drawdown_at_point(pt, wells, Q_list, params, method)

    # 深色主題繪圖
    with plt.style.context('dark_background'):
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        fig.patch.set_facecolor('#0F1729')
        ax.set_facecolor('#0F1729')

        # 洩降等值線 - 設定 0.5 間距
        z_min = np.min(Z)
        z_max = np.max(Z)
        
        # 不要畫出 s=0 (無洩降)，從 0.5 開始，或依照目前最低洩降
        min_level = math.floor(z_min * 2) / 2.0
        if min_level <= 0:
            min_level = 0.5
            
        max_level = math.ceil(z_max * 2) / 2.0
        # 確保至少有一個級距
        if max_level < min_level:
            max_level = min_level + 0.5
            
        # 產生 0.5 間距的陣列
        levels = np.arange(min_level, max_level + 0.5, 0.5)
        if len(levels) == 0:
            levels = np.array([0.5, 1.0])

        cs = ax.contourf(X, Y, Z, levels=levels, cmap='cool', alpha=0.85, extend='max')
        contour_lines = ax.contour(X, Y, Z, levels=levels, colors='#60A5FA',
                                    linewidths=0.5, alpha=0.6)
        
        # 標籤顯示到小數第一位
        ax.clabel(contour_lines, inline=True, fontsize=7, fmt='%.1f', colors='#CBD5E1')

        # 車站外框
        if station_coords:
            sx = [p[0] for p in station_coords] + [station_coords[0][0]]
            sy = [p[1] for p in station_coords] + [station_coords[0][1]]
            ax.plot(sx, sy, color='#F97316', linewidth=2.5, label='車站外框', zorder=4)
            ax.fill(sx, sy, alpha=0.08, color='#F97316')

        # 抽水井位置
        well_x = [w[0] for w in wells]
        well_y = [w[1] for w in wells]
        ax.scatter(well_x, well_y, c='#EF4444', s=80, zorder=5,
                   edgecolors='#FCA5A5', linewidths=1.5)
        for i, (wx, wy) in enumerate(wells):
            ax.annotate(f'W{i + 1}', (wx, wy), textcoords="offset points",
                        xytext=(5, 5), fontsize=9, color='#FCA5A5', fontweight='bold')

        # 參數標註
        method_name = 'Theis' if method == 'theis' else 'Neuman'
        info_lines = [
            f"Excav = {params.get('excavation_depth', 'N/A')} m",
            f"Head = {params.get('head', 'N/A')} m",
            f"S = {params.get('S', 'N/A')}",
            f"T = {params.get('T', 'N/A')} m²/day",
            f"t = {params.get('t', 'N/A')} day",
        ]
        if method == 'neuman':
            info_lines.extend([
                f"Sy = {params.get('Sy', 'N/A')}",
                f"Kh = {params.get('Kh', 'N/A')} m/day",
                f"Kv = {params.get('Kv', 'N/A')} m/day",
                f"b = {params.get('b', 'N/A')} m",
            ])
        info_text = '\n'.join(info_lines)
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
                verticalalignment='top', fontfamily='monospace', color='#CBD5E1',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#1E293B',
                          edgecolor='#334155', alpha=0.9))

        ax.set_xlabel('X (m)', fontsize=11, color='#94A3B8')
        ax.set_ylabel('Y (m)', fontsize=11, color='#94A3B8')
        title = f'{method_name} Drawdown Contour'
        ax.set_title(title, fontsize=14, fontweight='bold', color='#F1F5F9')

        ax.tick_params(colors='#64748B')
        for spine in ax.spines.values():
            spine.set_color('#334155')

        cbar = fig.colorbar(cs, ax=ax, shrink=0.85, pad=0.02, ticks=levels)
        cbar.set_label(f'{method_name} Drawdown (m)', fontsize=10, color='#94A3B8')
        cbar.ax.tick_params(colors='#64748B')

        ax.set_aspect('equal')
        fig.tight_layout()

    # 匯出 base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0F1729')
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_b64


# ─────────────────────────────────────────────
# 抽水井結果表格
# ─────────────────────────────────────────────
def build_result_table(wells, Q_list):
    """
    產生抽水井結果表格資料。
    包含 Q (CMD), QFS (CMD), QFS (GPM), Pump Type, Pump HP, Q-List (GPM)
    """
    results = []
    for i, Q in enumerate(Q_list):
        Q_cmd = round(Q, 1)
        # 安全係數 QFS = Q * 2.0 (常用 2 倍安全係數)
        Q_fs_cmd = round(Q * 2.0, 1)
        # 1 CMD = 0.18345 GPM (= 1000L/1440min * 0.264172)
        Q_fs_gpm = round(Q_fs_cmd * 1000 / 1440 * 0.264172, 1)

        # 泵浦選型建議
        if Q_fs_gpm <= 500:
            pump_type = 'RG30-2'
            pump_hp = 25
        elif Q_fs_gpm <= 1000:
            pump_type = 'RG35-2'
            pump_hp = 30
        elif Q_fs_gpm <= 2000:
            pump_type = 'RG40-2'
            pump_hp = 40
        elif Q_fs_gpm <= 3000:
            pump_type = 'RG50-2'
            pump_hp = 50
        else:
            pump_type = 'RG60-2'
            pump_hp = 60

        # Q-List (GPM) = Q_fs_gpm 的常見泵浦額定流量
        q_list_gpm = round(Q_fs_gpm * 0.7, 1)  # 大約 70% 為運轉點流量

        results.append({
            'name': f'W{i + 1}',
            'Q_cmd': Q_cmd,
            'Q_fs_cmd': Q_fs_cmd,
            'Q_fs_gpm': Q_fs_gpm,
            'pump_type': pump_type,
            'pump_hp': pump_hp,
            'q_list_gpm': q_list_gpm,
        })
    return results
