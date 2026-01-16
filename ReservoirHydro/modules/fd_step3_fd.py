import pandas as pd
import numpy as np
import io
import logging
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def auto_locator(data_min, data_max, target_ticks=7):
    """
    自動計算合適的 major 和 minor locator 間距

    Parameters:
    data_min, data_max: 資料的最小值和最大值
    target_ticks: 目標主刻度數量 (預設7個，會在5-10個之間)

    Returns:
    major_spacing, minor_spacing: 主刻度和次刻度間距
    """
    import math

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


def process_drainage_upload(uploaded_file):
    """
    處理排洪設施數據上傳

    Args:
        uploaded_file: Django UploadedFile 對象

    Returns:
        dict: 包含設施數據的字典，如果失敗則返回 None
    """
    try:
        logger.info("開始處理排洪設施數據檔案: %s", uploaded_file.name)

        # 🔧 修改：直接讀取名為 "出流" 的工作表
        try:
            outflow_df = pd.read_excel(uploaded_file, sheet_name="出流", header=None)
            logger.info("成功讀取 '出流' 工作表，數據形狀: %s", outflow_df.shape)
        except Exception as e:
            logger.error("讀取 '出流' 工作表失敗: %s", str(e))
            return None

        # 🔧 修改：使用新的解析邏輯
        facilities_data, q_power, q_start, q_end = parse_outflow_data(outflow_df)

        if not facilities_data:
            logger.error("沒有成功處理任何設施數據")
            return None

        result = {
            "facilities": facilities_data,
            "total_facilities": len(facilities_data),
        }

        logger.info("排洪設施數據處理完成，共 %d 個設施", len(facilities_data))
        return result, q_power, q_start, q_end

    except Exception as e:
        logger.error("排洪設施數據處理失敗: %s", str(e), exc_info=True)
        return None


def parse_outflow_data(outflow_df):
    """
    解析出流工作表數據

    Args:
        outflow_df: DataFrame 包含出流數據

    Returns:
        list: 設施數據列表
    """
    try:
        logger.info("開始解析出流數據")

        # === 基本設定資料擷取 ===
        q_power = int(outflow_df.iat[4, 0])  # 基本放水(發電)，是要傳出的參數
        q_start = int(outflow_df.iat[5, 0])  # 啟動條件，是要傳出的參數
        q_end = int(outflow_df.iat[6, 0])  # 結束條件，是要傳出的參數
        Sn = int(
            outflow_df.iat[0, 3]
        )  # 設施總數，不等於資料總數，因一個設施會有多個開度

        logger.info(
            "基本設定 - q_power: %d, q_start: %d, q_end: %d, 設施數: %d",
            q_power,
            q_start,
            q_end,
            Sn,
        )

        # === 設施資料擷取 ===
        facilities = []
        current_facility_id = 1

        # 建立設施字典來收集不同開度的數據
        facility_dict = {}

        num_openings = (outflow_df.shape[1] - 1) // 2
        for i in range(num_openings):
            try:
                # 檢查設施類型（開度）值
                stype_val = outflow_df.iat[2, 1 + 2 * i]
                if pd.isna(stype_val):
                    logger.warning("第 %d 個設施的開度值為空，跳過", i)
                    continue

                # 取得設施名稱和開度
                name_val = outflow_df.iat[1, 1 + 2 * i]
                if isinstance(stype_val, str) and stype_val.strip() == "全開":
                    opening_value = "全開"
                    logger.info("處理設施: %s, 開度: 全開, 列位置: %d", name_val, i)
                else:
                    try:
                        opening_value = float(stype_val)
                        logger.info(
                            "處理設施: %s, 開度: %s, 列位置: %d",
                            name_val,
                            opening_value,
                            i,
                        )
                    except (ValueError, TypeError):
                        logger.warning(
                            "第 %d 個設施的開度值 '%s' 無法解析，跳過", i, stype_val
                        )
                        continue

                logger.info(
                    "處理設施: %s, 開度: %s, 列位置: %d", name_val, opening_value, i
                )

                # 取得該開度的水位-流量數據
                rc_slice = outflow_df.iloc[5:, [1 + 2 * i, 2 + 2 * i]].dropna()

                if rc_slice.empty:
                    logger.warning(
                        "設施 '%s' 開度 %s 沒有有效數據", name_val, opening_value
                    )
                    continue

                # 重新命名欄位
                rc_slice.columns = ["WaterLevel", "Discharge"]
                rc_slice = rc_slice.astype(float).reset_index(drop=True)

                # 轉換為前端需要的格式
                opening_data = []
                for _, row in rc_slice.iterrows():
                    opening_data.append(
                        {
                            "water_level": float(row["WaterLevel"]),
                            "flow": float(row["Discharge"]),
                        }
                    )

                logger.info(
                    "設施 '%s' 開度 %s 處理完成，數據點數: %d",
                    name_val,
                    opening_value,
                    len(opening_data),
                )

                # 🔧 修改：按設施名稱分組，一個設施可以有多個開度
                if name_val not in facility_dict:
                    facility_dict[name_val] = {
                        "id": current_facility_id,
                        "name": name_val,
                        "openings": [],
                        "idx": current_facility_id - 1,  # 保持原有的 idx 概念
                    }
                    current_facility_id += 1

                # 添加該開度的數據到設施中
                facility_dict[name_val]["openings"].append(
                    {"opening": opening_value, "data": opening_data}
                )

            except Exception as e:
                logger.error("處理第 %d 個設施時發生錯誤: %s", i, str(e))
                continue

        # 轉換字典為列表
        facilities = list(facility_dict.values())

        # 檢查結果
        if not facilities:
            logger.error("沒有解析到任何有效的設施數據")
            return None

        # 按開度排序每個設施的開度數據
        for facility in facilities:
            # 🆕 自定義排序函數，處理「全開」的情況
            def sort_opening(opening_item):
                opening_value = opening_item["opening"]
                if opening_value == "全開":
                    return float("inf")  # 全開排在最後
                else:
                    try:
                        return float(opening_value)
                    except (ValueError, TypeError):
                        return float("inf")  # 無法解析的值也排在最後

            facility["openings"].sort(key=sort_opening)

            logger.info(
                "設施 '%s' 共有 %d 個開度: %s",
                facility["name"],
                len(facility["openings"]),
                [op["opening"] for op in facility["openings"]],
            )

        logger.info("出流數據解析完成，共 %d 個設施", len(facilities))
        return facilities, q_power, q_start, q_end

    except Exception as e:
        logger.error("解析出流數據失敗: %s", str(e), exc_info=True)
        return None


def validate_drainage_data(facilities_data):
    """
    驗證排洪設施數據

    Args:
        facilities_data: 設施數據字典

    Returns:
        tuple: (is_valid, error_messages)
    """
    is_valid = True
    error_messages = []

    try:
        if not facilities_data or "facilities" not in facilities_data:
            return False, ["無效的設施數據格式"]

        facilities = facilities_data["facilities"]

        if not facilities or len(facilities) == 0:
            return False, ["沒有找到任何設施數據"]

        for facility in facilities:
            # 檢查設施基本信息
            if "name" not in facility or "openings" not in facility:
                error_messages.append(
                    f"設施 '{facility.get('name', '未知')}' 缺少必要信息"
                )
                is_valid = False
                continue

            facility_name = facility["name"]
            openings = facility["openings"]

            if not openings or len(openings) == 0:
                error_messages.append(f"設施 '{facility_name}' 沒有開度數據")
                is_valid = False
                continue

            # 檢查開度數據
            for opening in openings:
                if "opening" not in opening or "data" not in opening:
                    error_messages.append(f"設施 '{facility_name}' 開度數據格式錯誤")
                    is_valid = False
                    continue

                opening_value = opening["opening"]
                data = opening["data"]

                if not data or len(data) == 0:
                    error_messages.append(
                        f"設施 '{facility_name}' 開度 {opening_value} 沒有數據點"
                    )
                    is_valid = False
                    continue

                # 檢查數據點格式
                for j, point in enumerate(data):
                    if "water_level" not in point or "flow" not in point:
                        error_messages.append(
                            f"設施 '{facility_name}' 開度 {opening_value} 第 {j+1} 個數據點格式錯誤"
                        )
                        is_valid = False
                        break

        if is_valid:
            logger.info("排洪設施數據驗證通過")
        else:
            logger.warning("排洪設施數據驗證失敗: %s", "; ".join(error_messages))

        return is_valid, error_messages

    except Exception as e:
        logger.error("排洪設施數據驗證過程中發生錯誤: %s", str(e))
        return False, [f"數據驗證失敗: {str(e)}"]


def generate_drainage_chart(facility_data):
    """
    生成排洪率定曲線圖表

    Args:
        facility_data: 單個設施的數據

    Returns:
        io.BytesIO: 圖片檔案的 BytesIO 物件，如果失敗則返回 None
    """
    try:
        logger.info("開始生成步驟3排洪率定曲線圖表")

        # 檢查數據
        if not facility_data or "openings" not in facility_data:
            logger.error("設施數據格式錯誤")
            return None

        openings = facility_data["openings"]
        if not openings:
            logger.error("沒有開度數據")
            return None

        # 設定中文字體
        plt.rcParams["font.sans-serif"] = [
            "Microsoft JhengHei",
            "SimHei",
            "Arial Unicode MS",
        ]
        plt.rcParams["axes.unicode_minus"] = False

        # 🔧 修改：創建圖表，使用新的風格
        fig, ax1 = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#e6f0fa")
        ax1.set_facecolor("white")

        # 🆕 添加：角度計算函數
        def get_angle(x, y, x_min, x_max, y_min, y_max, fig_width=10, fig_height=6):
            """
            根據資料 4/5 附近的五個點，考慮畫布比例（figsize），回傳標籤旋轉角度（degree）
            """
            # 用全域 min/max 標準化
            x_norm = (x - x_min) / (x_max - x_min) if x_max > x_min else x
            y_norm = (y - y_min) / (y_max - y_min) if y_max > y_min else y
            n = len(x)

            if n < 5:
                # 如果數據點少於5個，使用首尾兩點
                dx = x_norm[-1] - x_norm[0]
                dy = y_norm[-1] - y_norm[0]
            else:
                # 🔧 修改：計算 4/5 位置，取附近5個點
                target_pos = int(n * 0.8)  # 4/5 位置

                # 確保有足夠的點在目標位置附近
                start_idx = max(0, target_pos - 2)  # 向前取2個點
                end_idx = min(n, start_idx + 5)  # 總共5個點

                # 如果末端不夠5個點，調整起始位置
                if end_idx - start_idx < 5:
                    start_idx = max(0, end_idx - 5)

                # 取第一個和最後一個點計算斜率
                dx = x_norm[end_idx - 1] - x_norm[start_idx]
                dy = y_norm[end_idx - 1] - y_norm[start_idx]

            # 考慮畫布比例調整
            dx = dx / fig_height
            dy = dy / fig_width
            angle = np.degrees(np.arctan2(dy, dx))
            return angle

        # 🔧 修改：收集所有數據點以計算全域範圍
        all_x = []
        all_y = []

        for opening in openings:
            data = opening["data"]
            if data:
                flows = [point["flow"] for point in data]
                water_levels = [point["water_level"] for point in data]
                all_x.extend(flows)
                all_y.extend(water_levels)

        if not all_x or not all_y:
            logger.error("沒有有效的數據點")
            return None

        all_x = np.array(all_x)
        all_y = np.array(all_y)
        x_min, x_max = all_x.min(), all_x.max()
        y_min, y_max = all_y.min(), all_y.max()

        # 🔧 修改：先畫「全開」
        for opening in openings:
            opening_value = opening["opening"]
            data = opening["data"]

            if not data or opening_value != "全開":
                continue

            # 提取數據
            water_levels = np.array([point["water_level"] for point in data])
            flows = np.array([point["flow"] for point in data])

            # 繪製「全開」曲線
            ax1.plot(
                flows,
                water_levels,
                label="閘門全開",
                color="#1B1A57",
                linewidth=2.5,
                linestyle="-",
            )

            # 添加標籤
            if len(water_levels) > 0:
                frac = 0.8
                y_min_s, y_max_s = water_levels.min(), water_levels.max()
                y_label = y_min_s + frac * (y_max_s - y_min_s)
                x_label = np.interp(y_label, water_levels, flows)
                angle = get_angle(flows, water_levels, x_min, x_max, y_min, y_max)
                ax1.text(
                    x_label,
                    y_label,
                    "閘門全開",
                    color="#1B1A57",
                    fontsize=12,
                    va="center",
                    ha="left",
                    fontweight="bold",
                    rotation=angle,
                )

        # 🔧 修改：再畫其他開度
        for opening in openings:
            opening_value = opening["opening"]
            data = opening["data"]

            if not data or opening_value == "全開":
                continue

            # 提取數據
            water_levels = np.array([point["water_level"] for point in data])
            flows = np.array([point["flow"] for point in data])

            # 繪製其他開度曲線
            ax1.plot(
                flows,
                water_levels,
                label=f"開度 {opening_value} m",
                color="#1B1A57",
                linewidth=1.5,
                linestyle="--",
            )

            # 添加標籤
            if len(water_levels) > 0:
                frac = 0.8
                y_min_s, y_max_s = water_levels.min(), water_levels.max()
                y_label = y_min_s + frac * (y_max_s - y_min_s)
                x_label = np.interp(y_label, water_levels, flows)
                angle = get_angle(flows, water_levels, x_min, x_max, y_min, y_max)
                ax1.text(
                    x_label,
                    y_label,
                    f"開度 {opening_value} m",
                    color="#1B1A57",
                    fontsize=12,
                    va="center",
                    ha="left",
                    fontweight="bold",
                    rotation=angle,
                )

        # 🔧 修改：設定圖表標題和標籤
        facility_name = facility_data.get("name", "未知設施")
        ax1.set_title(
            f"{facility_name} - 排洪率定曲線", fontsize=16, fontweight="bold", pad=20
        )
        ax1.set_xlabel("流量 (cms)", fontsize=12)
        ax1.set_ylabel("水位 (m)", fontsize=12)

        # 🆕 添加：使用 auto_locator 自動設定刻度
        x_major, x_minor = auto_locator(x_min, x_max)
        y_major, y_minor = auto_locator(y_min, y_max)

        ax1.xaxis.set_major_locator(MultipleLocator(x_major))
        ax1.xaxis.set_minor_locator(MultipleLocator(x_minor))
        ax1.yaxis.set_major_locator(MultipleLocator(y_major))
        ax1.yaxis.set_minor_locator(MultipleLocator(y_minor))

        ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

        # 🆕 添加：設定軸範圍
        ax1.set_ylim(bottom=y_min)
        ax1.set_xlim(left=0)

        # 🆕 添加：設定網格
        ax1.grid(
            True,
            which="major",
            axis="x",
            linestyle="-",
            linewidth=1,
            color="black",
            alpha=0.5,
        )
        ax1.grid(
            True,
            which="major",
            axis="y",
            linestyle="-",
            linewidth=1,
            color="black",
            alpha=0.5,
        )
        ax1.grid(
            True,
            which="minor",
            axis="y",
            linestyle="--",
            linewidth=0.5,
            color="black",
            alpha=0.5,
        )

        # 調整布局
        plt.tight_layout()

        # 將圖表保存到 BytesIO
        buffer = io.BytesIO()
        plt.savefig(
            buffer,
            format="png",
            dpi=300,
            bbox_inches="tight",
            facecolor="#ffffff",  # 🔧 修改：使用新的背景色
            edgecolor="none",
        )
        buffer.seek(0)

        # 關閉圖表以釋放記憶體
        plt.close(fig)

        logger.info("步驟3排洪率定曲線圖表生成成功")
        return buffer

    except Exception as e:
        logger.error("步驟3圖表生成失敗: %s", str(e), exc_info=True)
        # 確保關閉圖表
        try:
            plt.close("all")
        except Exception:
            pass
        return None
