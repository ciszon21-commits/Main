"""
步驟1: 水庫庫容資料處理模組
"""

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import FuncFormatter
import io
import logging

matplotlib.use("Agg")  # 使用非互動式後端
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


def process_HAV_upload(uploaded_file):
    """處理水庫庫容數據上傳"""
    try:
        # 檢查檔案格式並使用對應的讀取方法
        file_name = uploaded_file.name.lower()

        if file_name.endswith(".csv"):
            # 讀取 CSV 檔案
            hav_df = pd.read_csv(uploaded_file, header=None)
        elif file_name.endswith((".xlsx", ".xlsm")):
            # 讀取 Excel 檔案，需要 openpyxl
            try:
                hav_df = pd.read_excel(
                    uploaded_file, sheet_name="HAV", header=None, engine="openpyxl"
                )
            except ValueError as e:
                if "No sheet named" in str(e):
                    # 如果沒有 "HAV" 工作表，讀取第一個工作表
                    hav_df = pd.read_excel(
                        uploaded_file, sheet_name=0, header=None, engine="openpyxl"
                    )
                else:
                    raise e
        elif file_name.endswith(".xls"):
            # 讀取舊版 Excel 檔案，需要 xlrd
            try:
                hav_df = pd.read_excel(
                    uploaded_file, sheet_name="HAV", header=None, engine="xlrd"
                )
            except ValueError as e:
                if "No sheet named" in str(e):
                    hav_df = pd.read_excel(
                        uploaded_file, sheet_name=0, header=None, engine="xlrd"
                    )
                else:
                    raise e
        else:
            raise ValueError("不支援的檔案格式")

        # print(f"讀取到的原始數據形狀: {hav_df.shape}")
        # print("前5行數據:")
        # print(hav_df.head())

        # 處理數據（從第3行開始，移除空值）
        hav_data = hav_df.iloc[2:].dropna(subset=[0, 1, 2]).reset_index(drop=True)
        hav_data.columns = (
            ["H", "A", "V", "Note"] if hav_data.shape[1] >= 4 else ["H", "A", "V"]
        )

        # 過濾掉 A=0 或 V=0 的數據 #! 確認要不要
        hav_data = hav_data[(hav_data["A"] != 0) & (hav_data["V"] != 0)].reset_index(
            drop=True
        )

        # 確保數據類型正確
        hav_data["H"] = pd.to_numeric(hav_data["H"], errors="coerce")
        hav_data["A"] = pd.to_numeric(hav_data["A"], errors="coerce")
        hav_data["V"] = pd.to_numeric(hav_data["V"], errors="coerce")

        # 移除轉換後的 NaN 值
        hav_data = hav_data.dropna(subset=["H", "A", "V"]).reset_index(drop=True)

        # print(f"處理後的數據形狀: {hav_data.shape}")
        # print("處理後的前5行:")
        # print(hav_data.head())

        # 檢查是否有有效數據
        if len(hav_data) == 0:
            raise ValueError("沒有找到有效的水庫庫容數據")

        # 直接返回 DataFrame
        return hav_data

    except ImportError as e:
        if "openpyxl" in str(e):
            raise ImportError("缺少 openpyxl 套件，請執行：pip install openpyxl") from e
        elif "xlrd" in str(e):
            raise ImportError("缺少 xlrd 套件，請執行：pip install xlrd") from e
        else:
            raise ImportError(f"套件導入錯誤: {str(e)}") from e

    except (ValueError, KeyError, TypeError, IOError) as e:
        # 更詳細的錯誤處理
        error_message = str(e)
        if "No sheet named" in error_message:
            return {
                "success": False,
                "message": '找不到名為 "HAV" 的工作表，請檢查 Excel 檔案格式',
            }
        elif "not found" in error_message.lower():
            return {"success": False, "message": "檔案讀取失敗，請確認檔案格式正確"}
        else:
            return {"success": False, "message": f"數據處理錯誤: {error_message}"}


def generate_hav_chart(hav_data):
    """
    生成 HAV (高度-面積-容量) 關係圖

    Args:
        hav_data: 包含水位、面積、容量數據的dataframe

    Returns:
        io.BytesIO: 圖片的二進制數據緩衝區，如果失敗則返回 None
    """
    try:
        H = hav_data["H"]
        H_min = H.min()
        A = hav_data["A"]
        V = hav_data["V"]

        logger.info("開始繪製 HAV 圖表，數據筆數: %d", len(H))

        # 設定中文字體
        plt.rcParams["font.sans-serif"] = [
            "Microsoft JhengHei",
            "SimHei",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False

        # 建立圖表 - 您可以在這裡實作您的 matplotlib 繪圖邏輯
        fig, ax1 = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#e6f0fa")
        ax1.set_facecolor("white")

        # 紅線：面積 vs 水位
        (p1,) = ax1.plot(A, H, color="red", linewidth=3)
        ax1.set_xlabel("面積 A ($m^{{2}}$)", color="red", fontsize=12)
        ax1.tick_params(axis="x", colors="red")
        ax1.invert_xaxis()
        ax1.set_ylabel("水位 H ($m$)", fontsize=12)
        ax1.set_xlim(right=0)

        # 自動設定刻度
        a_major, a_minor = auto_locator(A.min(), A.max())
        h_major, h_minor = auto_locator(H.min(), H.max())

        ax1.xaxis.set_major_locator(MultipleLocator(a_major))
        ax1.xaxis.set_minor_locator(MultipleLocator(a_minor))
        ax1.yaxis.set_major_locator(MultipleLocator(h_major))
        ax1.yaxis.set_minor_locator(MultipleLocator(h_minor))

        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax1.grid(
            True,
            which="major",
            axis="x",
            linestyle="-",
            linewidth=1,
            color="red",
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

        # 藍線：容量 vs 水位
        ax2 = ax1.twiny()
        (p2,) = ax2.plot(V, H, color="blue", linewidth=3)
        ax2.set_xlabel("容量 V ($m^{{3}}$)", color="blue", fontsize=12)
        ax2.tick_params(axis="x", colors="blue")
        ax2.set_xlim(left=0)
        ax2.set_ylim(bottom=H_min)

        # 自動設定容量軸刻度
        v_major, v_minor = auto_locator(V.min(), V.max())
        ax2.xaxis.set_major_locator(MultipleLocator(v_major))
        ax2.xaxis.set_minor_locator(MultipleLocator(v_minor))
        ax2.grid(
            True,
            which="major",
            axis="x",
            linestyle="-",
            linewidth=1,
            color="blue",
            alpha=0.5,
        )

        lines = [p1, p2]
        labels = ["水庫面積 ($m^{{2}}$)", "水庫容量 ($m^{{3}}$)"]
        ax2.legend(
            lines,
            labels,
            loc="center right",
            frameon=True,
            fontsize=12,
            fancybox=True,
            framealpha=1,
        )

        plt.tight_layout()
        plt.show()

        # 儲存到記憶體緩衝區
        buffer = io.BytesIO()
        plt.savefig(
            buffer,
            format="png",
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        buffer.seek(0)

        # 清理記憶體
        plt.close(fig)

        logger.info("HAV 圖表生成成功")
        return buffer

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("HAV 圖表生成失敗: %s", e)
        if "fig" in locals():
            plt.close(fig)
        return None


def validate_hav_data(data):
    """
    驗證 HAV 數據的有效性

    Args:
        data: 要驗證的數據

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        if not data or len(data) == 0:
            return False, "數據為空"

        required_fields = ["level", "area", "volume"]

        for i, row in enumerate(data):
            for field in required_fields:
                if field not in row:
                    return False, f"第 {i+1} 行缺少欄位: {field}"

                try:
                    float(row[field])
                except (ValueError, TypeError):
                    return False, f"第 {i+1} 行 {field} 欄位不是有效數值: {row[field]}"

        return True, ""

    except (ValueError, TypeError, KeyError) as e:
        return False, f"數據驗證錯誤: {str(e)}"
