"""
SRC柱設計計算引擎
完整複製 Excel ref/SRC柱設計.xlsx 的所有公式邏輯
"""
import math


def _round(val, ndigits=2):
    """模擬 Excel ROUND"""
    return round(val, ndigits)

def _fmt(val):
    """格式化數字以符合 Excel 的無多餘小數且無科學記號"""
    if val is None: return ""
    v = round(val, 4)
    if v == int(v): return str(int(v))
    return str(v)


def _rebar_area_single(size):
    """單根鋼筋面積 cm²"""
    mapping = {'#8': 5.067, '#10': 8.143, '#11': 10.07}
    return mapping.get(size, 5.067)


def _rebar_count_per_corner(config):
    """每個角落幾根"""
    return 3 if config == '每個角落配置3根' else 5


def _total_rebar_count(config):
    """總根數"""
    return _rebar_count_per_corner(config) * 4


def calculate_src_column(
    col_B, col_H, col_length,
    steel_b, steel_h, steel_t,
    rebar_config, rebar_size,
    cover_d, rebar_spacing,
    kx, ky,
    fys, steel_grade, fyr, fc,
    pu, mux, muy
):
    """
    SRC柱設計主計算函式

    Parameters:
    -----------
    col_B, col_H : int - SRC柱尺寸 (cm)
    col_length : float - 柱長度 (m)
    steel_b, steel_h, steel_t : int - 鋼骨尺寸 b×h×t (mm)
    rebar_config : str - '每個角落配置3根' 或 '每個角落配置5根'
    rebar_size : str - '#8', '#10', '#11'
    cover_d : float - d 保護層 (cm)
    rebar_spacing : float - 鋼筋間距 (cm)
    kx, ky : float - 有效長度係數
    fys : int - 鋼骨降伏強度 (kgf/cm²)
    steel_grade : str - 'SN490/SM490' 或 'SN400/SM400'
    fyr : int - 鋼筋降伏強度 (kgf/cm²)
    fc : int - 混凝土抗壓強度 fc' (kgf/cm²)
    pu : float - 設計軸力 (tf)
    mux, muy : float - 設計彎矩 (tf-m)

    Returns:
    --------
    dict - 包含 checks (檢核結果), calc (完整計算過程), lines (文字展示行)
    """
    Es = 2040000  # kgf/cm² 鋼骨彈性模數

    # ===== 基本計算 =====
    # Ry 係數
    Ry = 1.25 if steel_grade == 'SN400/SM400' else 1.2

    # 鋼骨保護層 (cm)
    steel_cover = min(col_B - steel_b / 10, col_H - steel_h / 10) / 2

    # ===== 鋼骨斷面性質 (箱型) =====
    b_cm = steel_b / 10  # mm → cm
    h_cm = steel_h / 10
    t_cm = steel_t / 10
    inner_b = b_cm - 2 * t_cm
    inner_h = h_cm - 2 * t_cm

    As = (b_cm * h_cm - inner_b * inner_h)  # cm²
    Isx = _round((b_cm * h_cm**3 - inner_b * inner_h**3) / 12, 2)  # cm⁴
    Isy = _round((h_cm * b_cm**3 - inner_h * inner_b**3) / 12, 2)  # cm⁴
    Zsx = _round((b_cm * h_cm**2 - inner_b * inner_h**2) / 4, 2)  # cm³
    Zsy = _round((h_cm * b_cm**2 - inner_h * inner_b**2) / 4, 2)  # cm³
    rsx = _round(math.sqrt(Isx / As), 2)  # cm
    rsy = _round(math.sqrt(Isy / As), 2)  # cm

    # ===== 寬厚比檢核 =====
    bt_ratio = (max(steel_b, steel_h) - steel_t) / steel_t
    bt_limit = _round(1.48 * math.sqrt(Es / Ry / fys), 2)
    bt_ok = bt_ratio < bt_limit

    # ===== 鋼骨比 =====
    rho_s = As / (col_B * col_H)
    rho_s_ok = rho_s > 0.02

    # ===== 鋼筋 =====
    n_per_corner = _rebar_count_per_corner(rebar_config)
    rebar_area_single = _rebar_area_single(rebar_size)
    Ar = n_per_corner * 4 * rebar_area_single  # 總鋼筋面積 cm²
    rho_r = Ar / (col_B * col_H)
    rho_r_ok = rho_r < 0.04

    # ===== EA / EI 剛度 =====
    Ec = 12000 * math.sqrt(fc)  # kgf/cm²
    EsAs = Es * As / 1000  # tf
    EcAc = _round(Ec * col_B * col_H / 1000, 2)  # tf
    EsIsx = _round(Es * Isx / 10000000, 2)  # tf-m²
    EsIsy = _round(Es * Isy / 10000000, 2)  # tf-m²
    EcIgx = _round(Ec / 10000000 / 12 * col_B * col_H**3, 2)  # tf-m²
    EcIgy = _round(Ec / 10000000 / 12 * col_H * col_B**3, 2)  # tf-m²

    # ===== 軸力彎矩分配 =====
    Pus = _round((EsAs / (EsAs + 0.55 * EcAc)) * pu, 2)
    Musx = _round((EsIsx / (EsIsx + 0.35 * EcIgx)) * mux, 2)
    Musy = _round((EsIsy / (EsIsy + 0.35 * EcIgy)) * muy, 2)

    # ===== 標稱受壓強度 Pns =====
    Ag = col_B * col_H

    # X 軸
    reff_x = _round(rsx + 0.2 * math.sqrt((col_B * col_H**3) / 12 / Ag), 2)
    lambda_cx = _round(kx * col_length * 100 * math.sqrt(fys / 1000 / 2040) / reff_x / math.pi, 2)
    if lambda_cx < 1.5:
        Pns_x = _round(math.exp(-0.419 * lambda_cx**2) * fys * As / 1000, 2)
        pns_x_formula = "exp(-0.419λc²)FysAs="
    else:
        Pns_x = _round((0.877 / lambda_cx**2) * fys * As / 1000, 2)
        pns_x_formula = "(0.877/λc²)FysAs="

    # Y 軸
    reff_y = _round(rsy + 0.2 * math.sqrt((col_H * col_B**3) / 12 / Ag), 2)
    lambda_cy = _round(ky * col_length * 100 * math.sqrt(fys / 1000 / 2040) / reff_y / math.pi, 2)
    if lambda_cy < 1.5:
        Pns_y = _round(math.exp(-0.419 * lambda_cy**2) * fys * As / 1000, 2)
        pns_y_formula = "exp(-0.419λc²)FysAs="
    else:
        Pns_y = _round((0.877 / lambda_cy**2) * fys * As / 1000, 2)
        pns_y_formula = "(0.877/λc²)FysAs="

    Pns_control = min(Pns_x, Pns_y)
    pns_control_axis = "Y" if Pns_y < Pns_x else "X"

    # ===== 鋼骨部分強度檢核 =====
    phi_cs = 0.85
    phi_bs = 0.9
    threshold_02 = 0.2 * phi_cs * Pns_control
    Mnsx = _round(Zsx * fys / 100000, 2)
    Mnsy = _round(Zsy * fys / 100000, 2)

    use_formula_b = Pus >= threshold_02

    if use_formula_b:
        steel_stress_ratio = _round(
            Pus / (phi_cs * Pns_control) + 8 / 9 * (Musx / (phi_bs * Mnsx) + Musy / (phi_bs * Mnsy)),
            3
        )
        formula_label = "b"
    else:
        steel_stress_ratio = _round(
            Pus / (2 * phi_cs * Pns_control) + (Musx / (phi_bs * Mnsx) + Musy / (phi_bs * Mnsy)),
            3
        )
        formula_label = "a"

    steel_check_ok = steel_stress_ratio <= 1.0

    # RC 部分鋼筋配置 (X軸彎矩: 中性軸平行X，沿Y軸計算深度，深度為 col_H)
    if rebar_config == '每個角落配置3根':
        n_layers = 4
        layer_areas = [
            4 * rebar_area_single,
            2 * rebar_area_single,
            2 * rebar_area_single,
            4 * rebar_area_single,
        ]
        layer_positions_x = [
            cover_d,
            cover_d + rebar_spacing,
            col_H - cover_d - rebar_spacing,
            col_H - cover_d,
        ]
        layer_positions_y = [
            cover_d,
            cover_d + rebar_spacing,
            col_B - cover_d - rebar_spacing,
            col_B - cover_d,
        ]
    else:
        n_layers = 6
        layer_areas = [
            6 * rebar_area_single,
            2 * rebar_area_single,
            2 * rebar_area_single,
            2 * rebar_area_single,
            2 * rebar_area_single,
            6 * rebar_area_single,
        ]
        layer_positions_x = [
            cover_d,
            cover_d + rebar_spacing,
            cover_d + 2 * rebar_spacing,
            col_H - cover_d - 2 * rebar_spacing,
            col_H - cover_d - rebar_spacing,
            col_H - cover_d,
        ]
        layer_positions_y = [
            cover_d,
            cover_d + rebar_spacing,
            cover_d + 2 * rebar_spacing,
            col_B - cover_d - 2 * rebar_spacing,
            col_B - cover_d - rebar_spacing,
            col_B - cover_d,
        ]

    # 重新精確計算 Ar (根據 Excel row 104)
    Ar = n_per_corner * 4 * rebar_area_single
    rho_r = Ar / (col_B * col_H)

    # β 係數 (重分配)
    beta = steel_stress_ratio
    # 檢查重分配後的力是否都為正
    Purc_test = pu - Pus / steel_stress_ratio
    Murcx_test = mux - Musx / steel_stress_ratio
    Murcy_test = muy - Musy / steel_stress_ratio
    if not (Purc_test > 0 and Murcx_test > 0 and Murcy_test > 0):
        beta = _round((max(Pus / pu, Musx / mux, Musy / muy) * 2 + 1) / 3, 3)

    Purc = _round(pu - Pus / beta, 2)
    Murcx = _round(mux - Musx / beta, 2)
    Murcy = _round(muy - Musy / beta, 2)

    # ===== (P0)rc 計算 =====
    P0rc_a = _round(0.8 * (0.85 * fc * (col_B * col_H - As - Ar) + Ar * fyr) / 1000, 2)
    P0rc_b = _round(0.8 * math.pi**2 * (EcIgx / 5) / ((kx * col_length)**2), 2)
    P0rc_c = _round(0.8 * math.pi**2 * (EcIgy / 5) / ((ky * col_length)**2), 2)
    P0rc = min(P0rc_a, P0rc_b, P0rc_c)

    # ===== β1 係數 =====
    beta1 = max(0.65, 0.85 - 0.05 * (fc - 280) / 70)
    if fc <= 280:
        beta1 = 0.85

    # ===== (Pnx)rc, (Pny)rc 中性軸迭代計算 =====
    def _solve_neutral_axis(target_ecc, layer_areas_list, layer_positions_list, depth, width):
        """
        迭代求中性軸位置
        target_ecc = M/P 偏心值
        depth = 彎矩方向之柱深（用於計算應變與抵抗彎矩）
        width = 垂直方向之柱寬（用於混凝土壓力面積）
        """
        P0_limit = P0rc_a  # 純軸壓上限

        # 先用二次方程式求初始假設的最小中性軸 (c_min)
        # Excel row 275: 二次方程式係數
        sum_comp_areas = sum(a for a, p in zip(layer_areas_list, layer_positions_list)
                            if p < depth / 2)  # approx comp side
        sum_tens_areas = sum(a for a, p in zip(layer_areas_list, layer_positions_list)
                            if p >= depth / 2)

        coeff_a = 0.85 * fc * beta1 * width
        coeff_b = sum(a * (0.003 * Es - 0.85 * fc) if p < beta1 * 999999 else -a * fyr
                      for a, p in zip(layer_areas_list, layer_positions_list))
        coeff_c = -sum(a * 0.003 * Es * p
                       for a, p in zip(layer_areas_list, layer_positions_list))

        # 實際公式
        coeff_b_actual = 0
        coeff_c_actual = 0
        for a_i, p_i in zip(layer_areas_list, layer_positions_list):
            coeff_b_actual += a_i * (0.003 * Es - 0.85 * fc)
        for a_i, p_i in zip(layer_areas_list, layer_positions_list):
            coeff_c_actual -= a_i * 0.003 * Es * p_i

        disc = coeff_b_actual**2 - 4 * coeff_a * coeff_c_actual
        if disc >= 0:
            c_min = (-coeff_b_actual + math.sqrt(disc)) / (2 * coeff_a)
        else:
            c_min = depth / 4

        # 40步迭代搜尋，從 depth 到 c_min
        step = (depth - c_min) / 40
        results = []
        for i in range(41):
            c = depth - step * i if i < 40 else c_min

            # 計算各層鋼筋受力
            rebar_forces = []
            for a_i, p_i in zip(layer_areas_list, layer_positions_list):
                strain = 0.003 / c * (c - p_i)
                stress = strain * Es
                # 限制在 ±fyr
                stress = max(-fyr, min(fyr, stress))
                # 減去混凝土應力（若在壓力區）
                if p_i < beta1 * c:
                    stress -= 0.85 * fc
                force = a_i * stress
                rebar_forces.append(force)

            # 混凝土壓力
            concrete_force = 0.85 * fc * beta1 * c * width

            # 總軸力 Pn
            Pn = (concrete_force + sum(rebar_forces)) / 1000
            Pn = min(Pn, P0_limit)  # 不超過P0rc

            # 彎矩 Mn
            Mn = (0.85 * fc * beta1 * c * width * (depth / 2 - beta1 * c / 2))
            for f_i, p_i in zip(rebar_forces, layer_positions_list):
                Mn += f_i * (depth / 2 - p_i)
            Mn = Mn / 100000  # → tf-m

            ecc = Mn / Pn if Pn != 0 else float('inf')

            results.append({
                'c': c,
                'forces': rebar_forces,
                'Pn': Pn,
                'Mn': Mn,
                'ecc': ecc,
            })

        # 線性內插求精確中性軸位置
        target = target_ecc
        best = None
        for i in range(len(results) - 1):
            r0 = results[i]
            r1 = results[i + 1]
            if (r0['ecc'] - target) * (r1['ecc'] - target) <= 0:
                # 內插
                if r0['ecc'] != r1['ecc']:
                    ratio = (target - r1['ecc']) / (r0['ecc'] - r1['ecc'])
                    c_interp = r1['c'] + ratio * (r0['c'] - r1['c'])
                else:
                    c_interp = (r0['c'] + r1['c']) / 2
                best = c_interp
                break

        if best is None:
            # 如果沒找到交叉點，取最接近的
            min_diff = float('inf')
            for r in results:
                diff = abs(r['ecc'] - target)
                if diff < min_diff:
                    min_diff = diff
                    best = r['c']

        # 用精確的中性軸位置計算最終結果
        c = best
        rebar_forces = []
        for a_i, p_i in zip(layer_areas_list, layer_positions_list):
            strain = 0.003 / c * (c - p_i)
            stress = strain * Es
            stress = max(-fyr, min(fyr, stress))
            if p_i < beta1 * c:
                stress -= 0.85 * fc
            force = a_i * stress
            rebar_forces.append(force)

        concrete_force = 0.85 * fc * beta1 * c * width
        Pn = (concrete_force + sum(rebar_forces)) / 1000
        Pn = min(Pn, P0_limit)
        Mn = (0.85 * fc * beta1 * c * width * (depth / 2 - beta1 * c / 2))
        for f_i, p_i in zip(rebar_forces, layer_positions_list):
            Mn += f_i * (depth / 2 - p_i)
        Mn = Mn / 100000
        ecc = _round(Mn / Pn, 4) if Pn != 0 else 0

        return {
            'c': _round(c, 2),
            'forces': [_round(f, 1) for f in rebar_forces],
            'Pn': _round(Pn, 2),
            'Mn': _round(Mn, 2),
            'ecc': ecc,
        }

    # X 軸方向 bending
    ecc_x = Murcx / Purc if Purc != 0 else 0
    result_x = _solve_neutral_axis(ecc_x, layer_areas, layer_positions_x, depth=col_H, width=col_B)
    Pnx_rc = result_x['Pn']
    Mnx_rc = result_x['Mn']

    # Y 軸方向 bending
    ecc_y = Murcy / Purc if Purc != 0 else 0
    result_y = _solve_neutral_axis(ecc_y, layer_areas, layer_positions_y, depth=col_B, width=col_H)
    Pny_rc = result_y['Pn']
    Mny_rc = result_y['Mn']

    # ===== Bresler Reciprocal Load Method =====
    Pnrc = _round(1 / (1 / Pnx_rc + 1 / Pny_rc - 1 / P0rc), 2)
    Pnrc_check_limit = 0.1 * P0rc
    Pnrc_ok = Pnrc > Pnrc_check_limit

    # RC 部分強度檢核
    phi_crc = 0.7
    phi_crc_Pnrc = _round(phi_crc * Pnrc, 3)
    rc_check_ok = phi_crc_Pnrc > Purc

    # ===== 軸向強度檢核 =====
    phi_Pn = _round(phi_cs * Pns_control + phi_crc_Pnrc, 3)
    pu_ratio = _round(pu / phi_Pn, 4)
    axial_ok = pu_ratio < 0.5

    # 鋼筋間距檢核文字
    if Purc <= 0.3 * col_B * col_H * fc / 1000 and fc <= 700:
        spacing_limit_text = "主筋間距需<30cm。"
    else:
        spacing_limit_text = "主筋間距需<20cm。"

    # ===== 組裝檢核結果 =====
    checks = {
        'Ry': Ry,
        'fys_check': {
            'value': fys,
            'limit': 4200,
            'op': '≤' if fys <= 4200 else '>',
            'result': 'OK' if fys <= 4200 else 'NG',
        },
        'fyr_check': {
            'value': fyr,
            'limit': 5600,
            'op': '≤' if fyr <= 5600 else '>',
            'result': 'OK' if fyr <= 5600 else 'NG',
        },
        'steel_cover': _round(steel_cover, 0),
        'bt_check': {
            'value': bt_ratio,
            'op': '<' if bt_ok else '>',
            'limit': bt_limit,
            'result': 'OK' if bt_ok else 'NG',
        },
        'rho_s_check': {
            'value': rho_s,
            'op': '>' if rho_s_ok else '<',
            'limit': 0.02,
            'result': 'OK' if rho_s_ok else 'NG',
            'note': '(一般建議約在4%至10%之間)',
        },
        'rho_r_check': {
            'value': rho_r,
            'op': '<' if rho_r_ok else '>',
            'limit': 0.04,
            'result': 'OK' if rho_r_ok else 'NG',
        },
        'steel_stress_ratio': {
            'value': steel_stress_ratio,
            'op': '≤' if steel_check_ok else '>',
            'limit': 1,
            'result': 'OK' if steel_check_ok else 'NG',
        },
        'rc_check': {
            'value': _round(phi_crc_Pnrc, 2),
            'op': '>' if rc_check_ok else '<',
            'limit': Purc,
            'result': 'OK' if rc_check_ok else 'NG',
        },
        'axial_check': {
            'value': pu_ratio,
            'op': '<' if axial_ok else '>',
            'limit': 0.5,
            'result': '不必檢核純軸壓強度' if axial_ok else '需額外檢核純軸壓強度',
        },
    }

    # ===== 組裝計算過程文字行 (模擬 Excel R35-R170) =====
    lines = _build_calculation_lines(
        col_B, col_H, col_length, steel_b, steel_h, steel_t,
        kx, ky, fys, steel_grade, fyr, fc, pu, mux, muy,
        Ry, steel_cover,
        As, Isx, Isy, Zsx, Zsy, rsx, rsy,
        bt_ratio, bt_limit, bt_ok,
        rho_s, rho_s_ok,
        EsAs, EcAc, EsIsx, EsIsy, EcIgx, EcIgy,
        Pus, Musx, Musy,
        reff_x, lambda_cx, Pns_x, pns_x_formula,
        reff_y, lambda_cy, Pns_y, pns_y_formula,
        Pns_control, pns_control_axis,
        threshold_02, Mnsx, Mnsy,
        use_formula_b, formula_label, steel_stress_ratio, steel_check_ok,
        rebar_config, rebar_size, Ar, rho_r, rho_r_ok,
        beta, Purc, Murcx, Murcy,
        P0rc_a, P0rc_b, P0rc_c, P0rc,
        n_layers, layer_areas, layer_positions_x, layer_positions_y,
        ecc_x, result_x, Pnx_rc, Mnx_rc,
        ecc_y, result_y, Pny_rc, Mny_rc,
        Pnrc, Pnrc_check_limit, Pnrc_ok,
        phi_crc_Pnrc, rc_check_ok,
        phi_Pn, pu_ratio, axial_ok,
        spacing_limit_text, n_per_corner,
    )

    return {
        'checks': checks,
        'lines': lines,
        'input': {
            'col_B': col_B, 'col_H': col_H, 'col_length': col_length,
            'steel_b': steel_b, 'steel_h': steel_h, 'steel_t': steel_t,
            'rebar_config': rebar_config, 'rebar_size': rebar_size,
            'cover_d': cover_d, 'rebar_spacing': rebar_spacing,
            'kx': kx, 'ky': ky,
            'fys': fys, 'steel_grade': steel_grade, 'fyr': fyr, 'fc': fc,
            'pu': pu, 'mux': mux, 'muy': muy,
        }
    }


def _build_calculation_lines(
    col_B, col_H, col_length, steel_b, steel_h, steel_t,
    kx, ky, fys, steel_grade, fyr, fc, pu, mux, muy,
    Ry, steel_cover,
    As, Isx, Isy, Zsx, Zsy, rsx, rsy,
    bt_ratio, bt_limit, bt_ok,
    rho_s, rho_s_ok,
    EsAs, EcAc, EsIsx, EsIsy, EcIgx, EcIgy,
    Pus, Musx, Musy,
    reff_x, lambda_cx, Pns_x, pns_x_formula,
    reff_y, lambda_cy, Pns_y, pns_y_formula,
    Pns_control, pns_control_axis,
    threshold_02, Mnsx, Mnsy,
    use_formula_b, formula_label, steel_stress_ratio, steel_check_ok,
    rebar_config, rebar_size, Ar, rho_r, rho_r_ok,
    beta, Purc, Murcx, Murcy,
    P0rc_a, P0rc_b, P0rc_c, P0rc,
    n_layers, layer_areas, layer_positions_x, layer_positions_y,
    ecc_x, result_x, Pnx_rc, Mnx_rc,
    ecc_y, result_y, Pny_rc, Mny_rc,
    Pnrc, Pnrc_check_limit, Pnrc_ok,
    phi_crc_Pnrc, rc_check_ok,
    phi_Pn, pu_ratio, axial_ok,
    spacing_limit_text, n_per_corner,
):
    """組裝計算過程的文字行列表（對應 Excel R35-R170）"""
    total_rebar = n_per_corner * 4

    fys_warning = ""
    if fys > 4200:
        fys_warning = "鋼骨降伏強度不宜大於4200kgf/cm²，NG"

    # 鋼筋面積/位置顯示
    if rebar_config == '每個角落配置3根':
        area_str = f"{_round(layer_areas[0], 3)}cm²、{_round(layer_areas[1], 3)}cm²、{_round(layer_areas[2], 3)}cm²、{_round(layer_areas[3], 3)}cm²"
        pos_str = f"{layer_positions_x[0]}cm、{layer_positions_x[1]}cm、{layer_positions_x[2]}cm、{layer_positions_x[3]}cm"
        pos_y_str = f"{layer_positions_y[0]}cm、{layer_positions_y[1]}cm、{layer_positions_y[2]}cm、{layer_positions_y[3]}cm"
    else:
        area_str = '、'.join([f"{_round(a, 3)}cm²" for a in layer_areas])
        pos_str = '、'.join([f"{p}cm" for p in layer_positions_x])
        pos_y_str = '、'.join([f"{p}cm" for p in layer_positions_y])

    forces_x_str = '、'.join([f"{f}kgf" for f in result_x['forces']])
    forces_y_str = '、'.join([f"{f}kgf" for f in result_y['forces']])

    sections = [
        {
            'title': '一、設計基本資料',
            'lines': [
                f"SRC柱全斷面尺寸為 {col_B}×{col_H} cm",
                f"柱長度為 {col_length} m",
                f"兩向有效長度係數分別為 Kx={kx}　Ky={ky}",
                f"鋼骨降伏強度Fys={fys} kgf/cm²　{steel_grade}",
                f"鋼筋降伏強度Fyr={fyr} kgf/cm²　混凝土抗壓強度fc'={fc} kgf/cm²",
                f"結構分析後作用於柱之最大軸力與彎矩為",
                f"Pu={pu} tf　Mux={mux} tf-m　Muy={muy} tf-m",
                fys_warning,
            ],
        },
        {
            'title': '二、鋼骨部分之設計',
            'lines': [
                f"1.選用鋼骨斷面□{steel_b}×{steel_h}×{steel_t}mm，此時鋼骨保護層為{int(steel_cover)}cm",
                "",
                f"檢核鋼骨斷面之寬厚比是否滿足λhd之規定",
                f"b/t=({max(steel_b, steel_h)}-{steel_t})/{steel_t}={bt_ratio:.0f} {'<' if bt_ok else '>'} 1.48√(Es/RyFys)={_fmt(bt_limit)}　{'OK' if bt_ok else 'NG'}",
                f"此箱型鋼骨斷面性質如下：",
                f"As={_fmt(As)} cm²　Isx={_fmt(Isx)} cm⁴　Isy={_fmt(Isy)} cm⁴",
                f"Zsx={_fmt(Zsx)} cm³　Zsy={_fmt(Zsy)} cm³　rsx={_fmt(rsx)} cm",
                f"rsy={_fmt(rsy)} cm",
                f"檢核鋼骨比ρs：",
                f"ρs=As/Ag={_fmt(_round(rho_s, 4))} {'>' if rho_s > 0.02 else '<'} 0.02　{'OK' if rho_s_ok else 'NG'}",
                "",
                f"2.軸力與彎矩分配：",
                "",
                f"(1)計算鋼骨部分與RC部分之軸向剛度EA與撓曲剛度EI:",
                f"EsAs={_fmt(EsAs)} tf　EcAc={_fmt(EcAc)} tf",
                f"EsIsx={_fmt(EsIsx)} tf-m²　EcIgx={_fmt(EcIgx)} tf-m²",
                f"EsIsy={_fmt(EsIsy)} tf-m²　EcIgy={_fmt(EcIgy)} tf-m²",
                "",
                f"(2)鋼骨分配之軸力與彎矩：",
                f"Pus=Pu×(EsAs/(EsAs+0.55EcAc))={_fmt(Pus)} tf",
                f"Musx=Mux×(EsIsx/(EsIsx+0.35EcIgx))={_fmt(Musx)} tf-m",
                f"Musy=Muy×(EsIsy/(EsIsy+0.35EcIgy))={_fmt(Musy)} tf-m",
                "",
                f"3.檢核鋼骨部分之強度：",
                "",
                f"(1)計算鋼骨部份之標稱受壓強度Pns",
                f"首先求出鋼骨之有效迴轉半徑reff及長細比參數λc，其中箱型鋼骨之α=0.2，再依公式計算Pns：",
                "",
                f"以X為軸",
                f"reff=rsx+α×√(Igx/Ag)={_fmt(reff_x)}",
                f"λc=KxL/πreff×√Fys/Es={_fmt(lambda_cx)} {'<' if lambda_cx < 1.5 else '>'} 1.5",
                f"Pns={pns_x_formula}{_fmt(Pns_x)} tf",
                "",
                f"以Y為軸",
                f"reff=rsy+α×√(Igy/Ag)={_fmt(reff_y)}",
                f"λc=KyL/πreff×√Fys/Es={_fmt(lambda_cy)} {'<' if lambda_cy < 1.5 else '>'} 1.5",
                f"Pns={pns_y_formula}{_fmt(Pns_y)} tf" + (f"　控制" if pns_control_axis == "Y" else ""),
                "",
                f"(2)檢核鋼骨部分之強度",
                f"a.當Pus<0.2φcsPns時，採用：",
                f"Pus/2φcsPns+(Musx/φbsMnsx+Musy/φbsMnsy)≤1",
                f"b.當Pus≥0.2φcsPns時，採用：",
                f"Pus/φcsPns+8/9×(Musx/φbsMnsx+Musy/φbsMnsy)≤1",
                "",
                f"0.2φcsPns=0.2×0.85×{_fmt(Pns_control)}={_fmt(_round(threshold_02, 4))} tf",
                f"Pus={_fmt(Pus)} {'>' if Pus >= threshold_02 else '<'} {_fmt(_round(threshold_02, 4))}　採用{formula_label}式檢核",
                f"其中，φbs=0.9",
                f"Mnsx=Zsx×Fys={_fmt(Mnsx)} tf-m　Mnsy=Zsy×Fys={_fmt(Mnsy)} tf-m",
                f"鋼骨部分應力比={_fmt(steel_stress_ratio)} {'≤' if steel_check_ok else '>'} 1　{'OK' if steel_check_ok else 'NG'}",
            ],
        },
        {
            'title': '三、RC部分之設計',
            'lines': [
                f"1.假設在SRC柱{rebar_config}{rebar_size}之主筋",
                f"Ar={_fmt(_round(Ar, 3))} cm²",
                f"ρr={_fmt(_round(rho_r, 4))} {'<' if rho_r < 0.04 else '>'} 0.04　{'OK' if rho_r_ok else 'NG'}",
                "",
                f"2.為求較經濟之設計結果，可依SRC規範第7.3.2節進行軸力與彎矩重新分配",
                f"根據上一節鋼骨部份之計算結果，得知軸力與彎矩重新分配係數最小可取至{_fmt(steel_stress_ratio)}",
                f"令β={_fmt(beta)}",
                f"故重新分配外力之後，RC部份所需分擔之軸力與彎矩如下：",
                f"Purc=Pu-Pus/β={_fmt(Purc)} tf",
                f"Murcx=Mux-Musx/β={_fmt(Murcx)} tf-m",
                f"Murcy=Muy-Musy/β={_fmt(Murcy)} tf-m",
                "",
                f"3.檢核RC部分之強度:",
                f"本例之柱受到軸力與雙軸向彎矩共同作用，若柱所受之軸力大於10%的純軸壓標稱強度，",
                f"則可採用Bresler的Reciprocal Load Method來求得Pnrc：",
                "",
                f"(1)(P0)rc之計算",
                f"(a)(P0)rc=0.8(0.85fc'Ac+ArFyr)={P0rc_a} tf",
                f"(b)(P0)rc=0.8(π²×EcIgx/5)/(KxL)²={P0rc_b} tf",
                f"(c)(P0)rc=0.8(π²×EcIgy/5)/(KyL)²={P0rc_c} tf",
                f"取小值　(P0)rc={P0rc} tf",
                "",
                f"(2)(Pnx)rc、(Pny)rc之計算",
                "",
                f"以X為軸",
                f"鋼筋共分為{n_layers}層，面積分別為{area_str}",
                f"鋼筋位置分別為{pos_str}",
                f"需分擔之外力偏心值為{Murcx}/{Purc}={_round(ecc_x, 4)}m",
                f"假設此時中性軸位於{result_x['c']}cm",
                f"則鋼筋受力分別為{forces_x_str}(壓為正，拉為負)",
                f"解出　(Pnx)rc={Pnx_rc} tf　(Mnx)rc={Mnx_rc} tf-m",
                f"驗證偏心值為 {result_x['ecc']} m",
                "",
                f"以Y為軸",
                f"鋼筋共分為{n_layers}層，面積分別為{area_str}",
                f"鋼筋位置分別為{pos_y_str}",
                f"需分擔之外力偏心值為{Murcy}/{Purc}={_round(ecc_y, 4)}m",
                f"假設此時中性軸位於{result_y['c']}cm",
                f"則鋼筋受力分別為{forces_y_str}(壓為正，拉為負)",
                f"解出　(Pny)rc={Pny_rc} tf　(Mny)rc={Mny_rc} tf-m",
                f"驗證偏心值為 {result_y['ecc']} m",
                "",
                f"(3)Pnrc之計算：",
                f"利用Bresler之Reciprocal Load Method求出Pnrc：",
                f"Pnrc={Pnrc} tf {'>' if Pnrc_ok else '<'} 0.1(P0)rc={_round(Pnrc_check_limit, 3)} tf　{'OK' if Pnrc_ok else 'NG'}",
                "",
                f"(4)檢核RC部分強度",
                f"φcrcPnrc={_fmt(phi_crc_Pnrc)} tf {'>' if rc_check_ok else '<'} {_fmt(Purc)} tf　{'OK' if rc_check_ok else 'NG'}",
            ],
        },
        {
            'title': '四、軸向強度檢核',
            'lines': [
                f"依SRC規範第9.3節規定",
                f"φPn=φcsPns+φcrcPnrc={_fmt(phi_Pn)} tf",
                f"Pu/φPn={_fmt(pu_ratio)} {'<' if axial_ok else '>'} 0.5　{'不必檢核純軸壓強度' if axial_ok else '需額外檢核純軸壓強度'}",
            ],
        },
        {
            'title': '五、設計結果',
            'lines': [
                f"本SRC柱最終之設計結果如下:",
                f"1.SRC柱全斷面尺寸：{col_B}cm×{col_H}cm",
                f"2.鋼骨斷面型式與尺寸：□{steel_b}X{steel_h}X{steel_t}({steel_grade})",
                f"3.主筋與補助筋配置:",
                f"(1)主筋採{rebar_config}{rebar_size}，共{total_rebar}根。",
                f"(2)依SRC規範第4.3.3節規定，SRC柱相鄰主筋之間距若大於30cm，應加配長向補助筋，其尺寸不得小於#4(D13)。",
                f"Purc>0.3Acfc'或fc'>700kgf/cm²時，間距不得大於20cm。",
                f"本柱在柱之每側{spacing_limit_text}",
            ],
        },
    ]

    return sections
