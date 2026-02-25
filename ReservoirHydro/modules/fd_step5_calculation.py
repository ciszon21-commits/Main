import io
import math
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import FuncFormatter
from matplotlib import rcParams
rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']


def run_flood_calculation(
    inflow_data: pd.DataFrame,
    initial_wl: float,
    H_arr: np.ndarray,
    V_arr: np.ndarray,
    structure_infos: list,
    q_start: float,
    q_power: float,
    q_end: float,
    step4_controls: list  # 步驟四控制條件
) -> pd.DataFrame:
    """
    複雜版排洪演算主流程，支援動態開度切換與設施關閉（狀態只在條件點切換，之後保持）
    - inflow_data: DataFrame，欄位需有 [時間, 流量]
    - initial_wl: 初始水位
    - H_arr, V_arr: HAV 曲線水位、容量陣列
    - structure_infos: 步驟3設施資訊
    - q_start, q_power, q_end: 步驟3參數
    - step4_controls: 步驟四控制條件 (list of dicts)
    回傳：結果 DataFrame
    """

    # 1. 整理設施所有開度資料
    facilities = []
    for idx, fac in enumerate(structure_infos):
        opening_dict = {}
        for op in fac.get("openings", []):
            opening_raw = op.get("opening", "")
            # 判斷型別
            if isinstance(opening_raw, (int, float)):
                # 如果是整數，轉成不帶小數點的字串
                if float(opening_raw).is_integer():
                    opening_val = str(int(opening_raw))
                else:
                    opening_val = str(opening_raw)
            else:
                # 字串直接 strip
                opening_val = str(opening_raw).strip()
            if "data" in op:
                df = pd.DataFrame(op["data"])
                h_col = [c for c in df.columns if "水位" in c or "level" in c.lower()]
                q_col = [c for c in df.columns if "流量" in c or "flow" in c.lower() or "discharge" in c.lower()]
                if h_col and q_col:
                    df = df.rename(columns={h_col[0]: "WaterLevel", q_col[0]: "Discharge"})
                    opening_dict[opening_val] = df
        facilities.append({
            "name": fac.get("name", f"設施{idx+1}"),
            "openings": opening_dict,
            "idx": idx
        })

    # 2. 整理步驟四控制條件 (facility+opening為key)
    for ctrl in step4_controls:
        for key in ["time_control", "flow_control_before", "flow_control_after", "waterlevel_control_before", "waterlevel_control_after"]:
            if key in ctrl and isinstance(ctrl[key], list):
                ctrl[key] = [str(x) if x != "" else "" for x in ctrl[key]]
    control_map = {}
    for ctrl in step4_controls:
        key = (ctrl["facility"], str(ctrl["opening"]))
        control_map.setdefault(key, []).append(ctrl)

    # 3. 計算流量洪峰時間
    inflow_arr = inflow_data["流量"].values if "流量" in inflow_data.columns else inflow_data["Flow"].values
    peak_flow_idx = np.argmax(inflow_arr)
    peak_flow_time = inflow_data.iloc[peak_flow_idx, 0]

    # 4. 主流程
    results = []
    header = ["時間(hr)", "流量(cms)", "總出流量(cms)", "水庫水位(m)", "水庫容量(m3)"] + \
        [f["name"] for f in facilities] + [f["name"]+"_開度" for f in facilities]

    Qp, Di = 0.0, 0.0
    QQ = 0.0
    wl = initial_wl
    s1 = hav_h_to_v(wl, H_arr, V_arr)
    t0, q0 = inflow_data.iloc[0, 0], inflow_data.iloc[0, 1]
    peak_wl_reached = False

    # 新增：每個設施維護目前開度狀態
    current_openings = [None for _ in facilities]

    # 計算開度狀態（只在條件點切換，之後保持）
    def update_opening(facility_idx, t, q, wl, last_t, last_q, last_wl, peak_flow_time, peak_wl_reached):
        fac = facilities[facility_idx]
        opening = current_openings[facility_idx]

        # 取得所有開度，排序：開度大的在前（全開最大）
        def opening_sort_key(val):
            if val == "全開":
                return float('inf')
            try:
                return float(val)
            except Exception:
                return -float('inf')
        sorted_openings = sorted(fac["openings"].keys(), key=opening_sort_key)
        for opening_val in sorted_openings:
            key = (fac["name"], opening_val)
            ctrls = control_map.get(key, [])
            for ctrl in ctrls:
                tc = ctrl.get("time_control", ["", ""])
                fcb = ctrl.get("flow_control_before", ["", ""])
                fca = ctrl.get("flow_control_after", ["", ""])
                wcb = ctrl.get("waterlevel_control_before", ["", ""])
                wca = ctrl.get("waterlevel_control_after", ["", ""])
                # 第一時段特別判斷
                if last_t is None and tc[0]:
                    if float(tc[0]) == t:
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 時間控制(起始) {tc[0]}，t={t}，設為開啟")
                        opening = opening_val
                # 時間控制
                if tc[0]:
                    if last_t is not None and last_t < float(tc[0]) <= t:
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 時間控制(起始) {tc[0]}，last_t={last_t}→t={t}，設為開啟")
                        opening = opening_val
                if tc[1]:
                    if last_t is not None and last_t < float(tc[1]) <= t:
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 時間控制(結束) {tc[1]}，last_t={last_t}→t={t}，設為關閉")
                        opening = None
                # 流量控制
                if fcb[0] and t <= peak_flow_time:
                    if last_q is not None and (
                        (last_q <= float(fcb[0]) <= q) or
                        (last_q >= float(fcb[0]) >= q)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰前流量控制(開啟) {fcb[0]}，last_q={last_q}→q={q}，設為開啟")
                        opening = opening_val
                if fcb[1] and t <= peak_flow_time:
                    if last_q is not None and (
                        (last_q <= float(fcb[1]) <= q) or
                        (last_q >= float(fcb[1]) >= q)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰前流量控制(關閉) {fcb[1]}，last_q={last_q}→q={q}，設為關閉")
                        opening = None
                if fca[0] and t > peak_flow_time:
                    if last_q is not None and (
                        (last_q <= float(fca[0]) <= q) or
                        (last_q >= float(fca[0]) >= q)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰後流量控制(開啟) {fca[0]}，last_q={last_q}→q={q}，設為開啟")
                        opening = opening_val
                if fca[1] and t > peak_flow_time:
                    if last_q is not None and (
                        (last_q <= float(fca[1]) <= q) or
                        (last_q >= float(fca[1]) >= q)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰後流量控制(關閉) {fca[1]}，last_q={last_q}→q={q}，設為關閉")
                        opening = None
                # 水位控制
                if wcb[0] and not peak_wl_reached:
                    if last_wl is not None and (
                        (last_wl <= float(wcb[0]) <= wl) or
                        (last_wl >= float(wcb[0]) >= wl)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰前水位控制(開啟) {wcb[0]}，last_wl={last_wl}→wl={wl}，設為開啟")
                        opening = opening_val
                if wcb[1] and not peak_wl_reached:
                    if last_wl is not None and (
                        (last_wl <= float(wcb[1]) <= wl) or
                        (last_wl >= float(wcb[1]) >= wl)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰前水位控制(關閉) {wcb[1]}，last_wl={last_wl}→wl={wl}，設為關閉")
                        opening = None
                if wca[0] and peak_wl_reached:
                    if last_wl is not None and (
                        (last_wl <= float(wca[0]) <= wl) or
                        (last_wl >= float(wca[0]) >= wl)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰後水位控制(開啟) {wca[0]}，last_wl={last_wl}→wl={wl}，設為開啟")
                        opening = opening_val
                if wca[1] and peak_wl_reached:
                    if last_wl is not None and (
                        (last_wl <= float(wca[1]) <= wl) or
                        (last_wl >= float(wca[1]) >= wl)
                    ):
                        # print(f"[{fac['name']}] 開度 {opening_val} 狀態變更: 洪峰後水位控制(關閉) {wca[1]}，last_wl={last_wl}→wl={wl}，設為關閉")
                        opening = None
        current_openings[facility_idx] = opening
        return opening

    # 計算出流
    def calc_outflow(ws, t, q, last_t, last_q, last_wl, peak_flow_time, peak_wl_reached):
        O_tot = 0.0
        Ot = []
        opening_rec = []
        for idx, fac in enumerate(facilities):
            opening_val = update_opening(idx, t, q, ws, last_t, last_q, last_wl, peak_flow_time, peak_wl_reached)
            opening_rec.append(opening_val if opening_val else "關閉")
            if opening_val and opening_val in fac["openings"]:
                df = fac["openings"][opening_val]
                h_arr = df["WaterLevel"].values
                q_arr = df["Discharge"].values
                if ws <= h_arr.min():
                    flow = 0.0
                elif ws >= h_arr.max():
                    flow = float(q_arr[-1])
                else:
                    f = interp1d(h_arr, q_arr)
                    flow = float(f(ws))
                flow = max(flow, 0.0)
            else:
                flow = 0.0
            Ot.append(flow)
            O_tot += flow
        return O_tot, Ot, opening_rec

    # 第一時段
    o1n, os1, open_rec1 = calc_outflow(wl, t0, q0, None, None, None, peak_flow_time, peak_wl_reached)
    Qfb = 0 if not (q0 < 6000 and q0 < Qp) else 1
    O1 = min(o1n, q0) if Qfb == 0 else 0.0
    if q0 <= q_start:
        O1 = q_power
    results.append([t0, q0, O1, wl, s1] + os1 + open_rec1)

    # 迴圈計算
    for i in range(1, len(inflow_data)):
        t, qi = inflow_data.iloc[i, 0], inflow_data.iloc[i, 1]
        if qi > Qp:
            Qp, QQ = qi, qi * 0.9
        Qfb = 1 if (qi < 6000 and qi < Qp) else 0
        I1, I2 = inflow_data.iloc[i - 1, 1], qi
        I_mean = (I1 + I2) / 2
        dt = (inflow_data.iloc[i, 0] - inflow_data.iloc[i - 1, 0]) * 3600
        s1 = results[-1][4]
        o1 = results[-1][2]
        Di = max(Di, I2 - I1)
        o2 = o1
        ncal = 0
        prev_wl = results[-1][3]

        # 疊代收斂
        while True:
            O_mean = (o1 + o2) / 2
            s2 = s1 + (I_mean - O_mean) * dt
            wl_temp = hav_v_to_h(s2, H_arr, V_arr)
            o2n, os_temp, open_rec2 = calc_outflow(
                wl_temp, t, qi,
                inflow_data.iloc[i-1, 0], inflow_data.iloc[i-1, 1], results[-1][3],
                peak_flow_time, peak_wl_reached
            )
            # 峰前/後及各種限制（可依需求調整）
            if Qfb == 0:
                o2n = o2n + q_power
                if I1 > q_start:
                    if o2n > I1:
                        o2n = I1
                    if o2n > Qp and I1 > QQ:
                        o2n = Qp
                else:
                    o2n = q_power
            else:
                if I1 <= q_end and o2n > I1:
                    o2n = I1
                if o2n > Qp:
                    o2n = Qp
            if o2n < q_power:
                o2n = q_power

            if o2 == 0 and o2n == 0:
                break
            if o2 != 0:
                if abs(o2n - o2) / o2 > 1e-7 and ncal < 300:
                    o2, ncal = (o2 + o2n) / 2, ncal + 1
                    continue
            else:
                if abs(o2n) > 1e-7 and ncal < 300:
                    o2, ncal = (o2 + o2n) / 2, ncal + 1
                    continue
            break

        if s2 < 0:
            results.append([t, qi, np.nan, np.nan, np.nan] + [np.nan] * len(facilities) + ["關閉"] * len(facilities))
            break
        wl2 = hav_v_to_h(s2, H_arr, V_arr)
        results.append([t, qi, o2n, wl2, s2] + os_temp + open_rec2)

        # 疊代結束後再判斷 peak_wl_reached
        if not peak_wl_reached and wl2 < prev_wl:
            peak_wl_reached = True
            print(f"[peak_wl_reached] 洪峰已過，t={t}，wl2={wl2}，prev_wl={prev_wl}")
        # elif peak_wl_reached:
            # print(f"[peak_wl_reached] 洪峰後，t={t}，wl2={wl2}，prev_wl={prev_wl}")
        # else:
            # print(f"[peak_wl_reached] 洪峰前，t={t}，wl2={wl2}，prev_wl={prev_wl}")

    df = pd.DataFrame(results, columns=header)
    return df


def run_flood_calculation_simple(
    inflow_data: pd.DataFrame,
    initial_wl: float,
    H_arr: np.ndarray,
    V_arr: np.ndarray,
    structure_infos: list,
    q_start: float,
    q_power: float,
    q_end: float
) -> pd.DataFrame:
    """
    簡易版排洪演算主流程
    - inflow_data: DataFrame，欄位需有 [時間, 流量]，建議欄位名為 ['Time', 'Flow']
    - initial_wl: 初始水位
    - H_arr, V_arr: HAV 曲線水位、容量陣列
    - structure_infos: 步驟3設施資訊，每個設施只取「全開」開度的資料
    - q_start, q_power, q_end: 步驟3參數
    回傳：結果 DataFrame
    """

    # 1. 準備設施全開資料
    facilities = []
    for idx, fac in enumerate(structure_infos):
        # 只取開度=全開的資料
        full_open = None
        for op in fac.get("openings", []):
            if str(op.get("opening", "")).strip() == "全開":
                full_open = op
                break
        if full_open and "data" in full_open:
            # 轉成 DataFrame
            df = pd.DataFrame(full_open["data"])
            # 欄位標準化
            h_col = [c for c in df.columns if "水位" in c or "level" in c.lower()]
            q_col = [c for c in df.columns if "流量" in c or "flow" in c.lower() or "discharge" in c.lower()]
            if h_col and q_col:
                df = df.rename(columns={h_col[0]: "WaterLevel", q_col[0]: "Discharge"})
                facilities.append({
                    "name": fac.get("name", f"設施{idx+1}"),
                    "data": df,
                    "idx": idx
                })
    if not facilities:
        raise ValueError("未找到任何設施的全開資料")

    # 2. 準備主流程
    results = []
    header = ["時間(hr)", "流量(cms)", "總出流量(cms)", "水庫水位(m)", "水庫容量(m3)"] + [f["name"] for f in facilities]

    # 3. 初始條件
    Qp, Di = 0.0, 0.0
    QQ = 0.0  # Initialize QQ to avoid using before assignment
    wl = initial_wl
    s1 = hav_h_to_v(wl, H_arr, V_arr)
    t0, q0 = inflow_data.iloc[0, 0], inflow_data.iloc[0, 1]

    # 計算第一時段總出流
    def calc_outflow(ws):
        O_tot = 0.0
        Ot = []
        for fac in facilities:
            df = fac["data"]
            h_arr = df["WaterLevel"].values
            q_arr = df["Discharge"].values
            # 線性內插
            if ws <= h_arr.min():
                flow = 0.0
            elif ws >= h_arr.max():
                flow = float(q_arr[-1])
            else:
                f = interp1d(h_arr, q_arr)
                flow = float(f(ws))
            flow = max(flow, 0.0)
            Ot.append(flow)
            O_tot += flow
        return O_tot, Ot

    o1n, os1 = calc_outflow(wl)
    Qfb = 0 if not (q0 < 6000 and q0 < Qp) else 1
    O1 = min(o1n, q0) if Qfb == 0 else 0.0
    if q0 <= q_start:
        O1 = q_power
    results.append([t0, q0, O1, wl, s1] + os1)

    # 4. 循環計算
    for i in range(1, len(inflow_data)):
        t, qi = inflow_data.iloc[i, 0], inflow_data.iloc[i, 1]
        if qi > Qp:
            Qp, QQ = qi, qi * 0.9
            # Qp, Qpo, QQ = qi, 6000, qi * 0.9
        Qfb = 1 if (qi < 6000 and qi < Qp) else 0
        I1, I2 = inflow_data.iloc[i - 1, 1], qi
        I_mean = (I1 + I2) / 2
        dt = (inflow_data.iloc[i, 0] - inflow_data.iloc[i - 1, 0]) * 3600
        s1 = results[-1][4]
        o1 = results[-1][2]
        Di = max(Di, I2 - I1)
        o2 = o1
        ncal = 0

        # 疊代收斂
        while True:
            O_mean = (o1 + o2) / 2
            s2 = s1 + (I_mean - O_mean) * dt
            wl_temp = hav_v_to_h(s2, H_arr, V_arr)
            o2n, os_temp = calc_outflow(wl_temp)
            # 峰前/後及各種限制
            if Qfb == 0:
                o2n = o2n + q_power
                if I1 > q_start:
                    if o2n > I1:
                        o2n = I1
                    if o2n > Qp and I1 > QQ:
                        o2n = Qp
                else:
                    o2n = q_power
            else:
                if I1 <= q_end and o2n > I1:
                    o2n = I1
                if o2n > Qp:
                    o2n = Qp
            if o2n < q_power:
                o2n = q_power

            if o2 == 0 and o2n == 0:
                break
            if o2 != 0:
                if abs(o2n - o2) / o2 > 1e-7 and ncal < 300:
                    o2, ncal = (o2 + o2n) / 2, ncal + 1
                    continue
            else:
                if abs(o2n) > 1e-7 and ncal < 300:
                    o2, ncal = (o2 + o2n) / 2, ncal + 1
                    continue
            break

        if s2 < 0:
            print(f"Warning: Negative reservoir volume at time {t}.")
            results.append([t, qi, np.nan, np.nan, np.nan] + [np.nan] * len(facilities))
            break
        wl2 = hav_v_to_h(s2, H_arr, V_arr)
        results.append([t, qi, o2n, wl2, s2] + os_temp)

    df = pd.DataFrame(results, columns=header)
    return df


def hav_h_to_v(xa, H, V, N=5):
    """
    與 VBA 演算法一致的水位到容量 Lagrange 插值
    xa: 水位
    H:  水位陣列
    V:  容量陣列
    """
    n = len(H)
    N = min(N, n)
    # 找區段
    i = np.searchsorted(H, xa) - 1
    i = max(0, min(i, n - 2))
    half = N // 2
    # VBA 版偏移量 +1
    start = i - half + 1
    if start < 0:
        start = 0
    if start > n - N:
        start = n - N
    end = start + N

    ya = 0.0
    for k in range(start, end):
        term = V[k]
        for j in range(start, end):
            if j != k:
                term *= (xa - H[j]) / (H[k] - H[j])
        ya += term
    return ya


def hav_v_to_h(xv, H, V, N=5):
    """
    與 VBA 演算法一致的容量到水位 Lagrange 反向插值
    xv: 容量
    H:  水位陣列
    V:  容量陣列
    """
    n = len(V)
    N = min(N, n)
    # 找區段
    i = np.searchsorted(V, xv) - 1
    i = max(0, min(i, n - 2))
    half = N // 2
    # VBA 版偏移量 +1
    start = i - half + 1
    if start < 0:
        start = 0
    if start > n - N:
        start = n - N
    end = start + N

    ya = 0.0
    for k in range(start, end):
        term = H[k]
        for j in range(start, end):
            if j != k:
                term *= (xv - V[j]) / (V[k] - V[j])
        ya += term
    return ya


def auto_locator(data_min, data_max, target_ticks=7):
    """
    自動計算合適的 major 和 minor locator 間距

    Parameters:
    data_min, data_max: 資料的最小值和最大值
    target_ticks: 目標主刻度數量 (預設7個，會在5-10個之間)

    Returns:
    major_spacing, minor_spacing: 主刻度和次刻度間距
    """

    # 計算資料範圍
    data_range = data_max - data_min
    if data_range == 0:
        return 1, 0.2

    # 計算大概的間距
    rough_spacing = data_range / target_ticks

    # 找到最接近的「好看」數字 (1, 2, 5 的倍數)
    magnitude = 10 ** math.floor(math.log10(rough_spacing))
    normalized = rough_spacing / magnitude

    if normalized <= 1.5:
        nice_spacing = 1 * magnitude
    elif normalized <= 3:
        nice_spacing = 2 * magnitude
    elif normalized <= 7:
        nice_spacing = 5 * magnitude
    else:
        nice_spacing = 10 * magnitude

    major_spacing = nice_spacing
    minor_spacing = major_spacing / 5

    return major_spacing, minor_spacing


def generate_final_chart(df):
    """
    產生最終排洪演算結果圖表
    輸入: df (pandas.DataFrame) - 欄位需包含 ['時間(hr)', '流量(cms)', '總出流量(cms)', '水庫水位(m)']
    回傳: BytesIO 物件 (PNG 圖片)
    """
    # 1. 取得資料
    t = df['時間(hr)']
    inflow = df['流量(cms)']
    outflow = df['總出流量(cms)']
    waterlevel = df['水庫水位(m)']

    # 2. 計算 y1/y2 軸上下限與刻度（完全比照 fd-charts.js）
    # y1: 流量 (cms)
    maxFlow = max(inflow.max(), outflow.max())
    y1_min = 0
    y1_step = 500
    y1_max = math.ceil(int(maxFlow) / 332) * 500
    if y1_max == maxFlow:
        y1_max += y1_step
    y_tick_count = int((y1_max - y1_min) / y1_step) + 1

    # y2: 水位 (m)
    wl_min = waterlevel.min()
    wl_max = waterlevel.max()
    wl_range = wl_max - wl_min
    y2_step = 10
    if wl_range > 0:
        step_candidates = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
        for step in step_candidates:
            if wl_range < step * 2:
                y2_step = step
                break
    y2_max = math.ceil(wl_max / 10) * 10 + 10
    y2_min = y2_max - y2_step * (y_tick_count - 1)
    # 若 wl_min < y2_min，則再往下補一格
    while wl_min < y2_min:
        y2_min -= y2_step
        y2_max -= y2_step

    # x: 時間 (hr)
    t_max = t.max()
    x_max = math.ceil(t_max / 10) * 10

    # 3. 找最大點
    idx_max = waterlevel.idxmax()
    t_max = t[idx_max]
    lvl_max = waterlevel[idx_max]
    idx_max_flow = inflow.idxmax()
    t_max_flow = t[idx_max_flow]
    flow_max_value = inflow[idx_max_flow]
    idx_max_out = outflow.idxmax()
    t_max_out = t[idx_max_out]
    out_max_value = outflow[idx_max_out]

    # 4. 畫圖
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#e6f0fa')
    ax1.set_facecolor('white')

    # 主軸：流量
    p1, = ax1.plot(t, inflow, marker='o', mfc="#EEECD0", color='#EE8A29', label='總入流量 (cms)', linewidth=3)
    p2, = ax1.plot(t, outflow, marker='s', mfc='#EEECD0', color='#1F5FA5', label='總出流量 (cms)', linewidth=3)
    ax1.set_xlabel('歷時 (hr)', fontsize=12)
    ax1.set_ylabel('流量 (cms)', fontsize=12)
    ax1.set_xlim(t.min(), x_max)
    ax1.set_ylim(y1_min, y1_max)
    ax1.yaxis.set_major_locator(MultipleLocator(y1_step))
    ax1.yaxis.set_minor_locator(MultipleLocator(y1_step/5))
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax1.grid(True, which='major', axis='y', linestyle='-', linewidth=1, color='black', alpha=0.5)
    ax1.grid(True, which='minor', axis='y', linestyle='--', linewidth=0.5, color='black', alpha=0.3)
    ax1.grid(True, which='major', axis='x', linestyle='-', linewidth=1, color='black', alpha=0.5)

    # 副軸：水位
    ax2 = ax1.twinx()
    p3, = ax2.plot(t, waterlevel, '-', color='#2E8B57', label='水庫水位 (m)', linewidth=3)
    ax2.set_ylabel('水位 (m)', fontsize=12)
    ax2.set_ylim(y2_min, y2_max)
    ax2.yaxis.set_major_locator(MultipleLocator(y2_step))
    ax2.yaxis.set_minor_locator(MultipleLocator(y2_step/5))
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax2.grid(False)

    # 讓左右y軸格線對齊
    ax2.set_yticks([y2_min + i*y2_step for i in range(y_tick_count)])

    # 標註最高水位點
    ax2.annotate(
        f'水庫最高水位\nEL. {lvl_max:,.2f} m',
        xy=(t_max, lvl_max), xytext=(t_max+5, lvl_max+2.5),
        arrowprops=dict(arrowstyle='->', color="#2E8B57"),
        color='#1B5233', fontsize=12,
        bbox=dict(boxstyle='round,pad=0.5', fc="#FFFFFF", ec="#2E8B57", alpha=1)
    )

    # 標註最大入流量
    ax1.annotate(
        f'最大總入流量\n$Q_{{in,max}}$ = {flow_max_value:,.0f} cms',
        xy=(t_max_flow, flow_max_value), xytext=(t_max_flow-20, flow_max_value+300),
        arrowprops=dict(arrowstyle='->', color="#EE8A29"),
        color='#AA641D', fontsize=12,
        bbox=dict(boxstyle='round,pad=0.5', fc="#FFFFFF", ec="#EE8A29", alpha=1)
    )

    # 標註最大出流量
    ax1.annotate(
        f'最大總出流量\n$Q_{{out,max}}$ = {out_max_value:,.0f} cms',
        xy=(t_max_out, out_max_value), xytext=(t_max_out+5, out_max_value+300),
        arrowprops=dict(arrowstyle='->', color="#1F5FA5"),
        color="#153E6B", fontsize=12,
        bbox=dict(boxstyle='round,pad=0.5', fc="#FFFFFF", ec="#1F5FA5", alpha=1)
    )

    # 圖例
    lines = [p1, p2, p3]
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc=6, bbox_to_anchor=(0, 0.5), frameon=True, fontsize=12, fancybox=True, framealpha=1)
    plt.tight_layout()

    # 存成 BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf
