"""
步驟2: 入流流量歷線處理模組
"""

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import FuncFormatter
import io
import logging
import numpy as np
from scipy.interpolate import interp1d

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


def process_inflow_upload(uploaded_file):
    """
    處理入流流量歷線檔案上傳

    Args:
        uploaded_file: 上傳的 Excel 檔案

    Returns:
        tuple: (inflow_data, initial_wl) 或 (None, None) 如果處理失敗
    """
    try:
        logger.info("開始處理入流流量歷線檔案")

        # 驗證檔案格式
        if not uploaded_file.name.lower().endswith(('.xlsx', '.xlsm', '.xls')):
            logger.error("不支援的檔案格式: %s", uploaded_file.name)
            raise ValueError("檔案格式錯誤，請上傳 Excel 檔案(.xlsx, .xlsm 或 .xls)")

        logger.info("處理檔案: %s", uploaded_file.name)

        # 讀取 Excel 檔案的「入流」工作表
        try:
            inflow_df = pd.read_excel(uploaded_file, sheet_name="入流", header=None)
            logger.info("成功讀取工作表，原始數據形狀: %s", inflow_df.shape)
        except Exception as e:
            logger.error("讀取工作表失敗: %s", e)
            raise ValueError("無法讀取「入流」工作表，請檢查檔案格式和工作表名稱") from e

        # 驗證檔案結構
        if inflow_df.empty:
            logger.error("工作表為空")
            raise ValueError("檔案內容為空")

        if inflow_df.shape[1] < 4:
            logger.error("欄位數量不足: %s", inflow_df.shape[1])
            raise ValueError("檔案格式錯誤，至少需要4個欄位")

        # 提取初始水位
        try:
            if pd.isna(inflow_df.iat[0, 3]):
                logger.error("初始水位欄位為空")
                raise ValueError("找不到初始水位數據（第1行第4欄）")

            initial_wl = float(inflow_df.iat[0, 3])
            logger.info("初始水位: %s", initial_wl)

            # 驗證初始水位合理性
            if initial_wl < 0:
                logger.warning("初始水位為負值: %s", initial_wl)
            if initial_wl > 2000:  # 假設水位不會超過2000米
                logger.warning("初始水位異常高: %s", initial_wl)

        except (ValueError, IndexError) as e:
            logger.error("初始水位轉換失敗: %s", e)
            raise ValueError("初始水位格式錯誤，請確保第1行第4欄為有效數值") from e

        # 處理入流數據
        try:
            # 從第二行開始提取數據，移除時間和流量欄位為空的行
            _inflow_tmp = inflow_df.iloc[1:].dropna(subset=[0, 1])
            logger.info("移除空白行後數據形狀: %s", _inflow_tmp.shape)

            if _inflow_tmp.empty:
                logger.error("入流數據為空")
                raise ValueError("沒有找到有效的入流數據")

            # 設定欄位名稱
            _inflow_tmp.columns = ["Time", "Flow", "nan1", "nan2"]

            # 提取時間和流量欄位
            inflow_data = _inflow_tmp[["Time", "Flow"]].dropna().iloc[1:].reset_index(drop=True)
            logger.info("最終處理後數據形狀: %s", inflow_data.shape)

            if inflow_data.empty:
                logger.error("處理後入流數據為空")
                raise ValueError("沒有找到有效的時間-流量數據對")

            # 轉換數據類型
            try:
                inflow_data = inflow_data.astype(float)
                logger.info("數據類型轉換成功")
            except ValueError as e:
                logger.error("數據類型轉換失敗: %s", e)
                raise ValueError("時間或流量數據包含非數值內容，請檢查數據格式") from e

            # 驗證數據合理性
            time_values = inflow_data["Time"].values
            flow_values = inflow_data["Flow"].values

            # 檢查時間序列
            if len(time_values) < 2:
                logger.error("數據點太少: %d", len(time_values))
                raise ValueError("入流數據點數量不足，至少需要2個數據點")

            # 檢查時間是否為遞增序列
            if not all(time_values[i] <= time_values[i+1] for i in range(len(time_values)-1)):
                logger.warning("時間序列不是嚴格遞增的")

            # 檢查時間範圍合理性
            if time_values.min() < 0:
                logger.warning("存在負時間值: %s", time_values.min())
            if time_values.max() > 365 * 24:  # 假設不超過一年的小時數
                logger.warning("時間值異常大: %s", time_values.max())

            # 檢查流量範圍合理性
            if flow_values.min() < 0:
                logger.warning("存在負流量值: %s", flow_values.min())
            if flow_values.max() > 100000:  # 假設流量不超過100,000
                logger.warning("流量值異常大: %s", flow_values.max())

            # 統計信息
            logger.info("時間範圍: %.3f ~ %.3f", time_values.min(), time_values.max())
            logger.info("流量範圍: %.3f ~ %.3f", flow_values.min(), flow_values.max())
            logger.info("平均流量: %.3f", flow_values.mean())

            # 檢查是否有重複的時間點
            if len(time_values) != len(set(time_values)):
                duplicates = len(time_values) - len(set(time_values))
                logger.warning("發現 %d 個重複的時間點", duplicates)

            logger.info("入流流量歷線處理完成")
            return inflow_data, initial_wl

        except Exception as e:
            logger.error("入流數據處理失敗: %s", e)
            raise ValueError(f"入流數據處理失敗: {str(e)}") from e

    except (ValueError, IndexError, pd.errors.EmptyDataError, TypeError) as e:
        logger.error("入流流量歷線處理失敗: %s", e)
        return None, None


def validate_inflow_data(inflow_data, initial_wl):
    """
    驗證入流數據的完整性和合理性

    Args:
        inflow_data: pandas DataFrame，包含時間和流量數據
        initial_wl: float，初始水位

    Returns:
        tuple: (is_valid, error_messages)
    """
    try:
        error_messages = []

        # 檢查數據框結構
        if inflow_data is None or inflow_data.empty:
            return False, ["入流數據為空"]

        required_columns = ["Time", "Flow"]
        missing_columns = [col for col in required_columns if col not in inflow_data.columns]
        if missing_columns:
            error_messages.append(f"缺少必要欄位: {missing_columns}")

        # 檢查數據類型
        for col in required_columns:
            if col in inflow_data.columns:
                if not pd.api.types.is_numeric_dtype(inflow_data[col]):
                    error_messages.append(f"{col} 欄位包含非數值數據")

        # 檢查初始水位
        if initial_wl is None:
            error_messages.append("初始水位為空")
        elif not isinstance(initial_wl, (int, float)):
            error_messages.append("初始水位不是數值類型")

        # 檢查數據完整性
        if not error_messages:  # 只有在基本檢查通過後才進行詳細檢查
            # 檢查 NaN 值
            if inflow_data.isnull().any().any():
                nan_counts = inflow_data.isnull().sum()
                error_messages.append(f"數據包含空值: {nan_counts.to_dict()}")

            # 檢查重複時間
            if inflow_data["Time"].duplicated().any():
                duplicate_count = inflow_data["Time"].duplicated().sum()
                error_messages.append(f"發現 {duplicate_count} 個重複的時間點")

            # 檢查數據範圍
            time_range = inflow_data["Time"].max() - inflow_data["Time"].min()
            if time_range <= 0:
                error_messages.append("時間範圍無效")

            flow_negative_count = (inflow_data["Flow"] < 0).sum()
            if flow_negative_count > 0:
                error_messages.append(f"發現 {flow_negative_count} 個負流量值")

        is_valid = len(error_messages) == 0
        return is_valid, error_messages

    except (ValueError, TypeError) as e:
        logger.error("數據驗證失敗: %s", e)
        return False, [f"數據驗證失敗: {str(e)}"]


def adjust_inflow_upload(inflow_data, delta_t):
    """
    調整入流數據的時間間距

    Args:
        inflow_data: pandas DataFrame 或 list，原始入流數據
                    如果是 DataFrame，需包含 'Time' 和 'Flow' 欄位
                    如果是 list，每個元素需為包含 'Time' 和 'Flow' 鍵的字典
        delta_t: float，新的時間間距 (小時)

    Returns:
        pandas DataFrame: 調整後的入流數據，包含 'Time' 和 'Flow' 欄位

    Raises:
        ValueError: 當輸入數據格式錯誤或參數無效時
        TypeError: 當輸入數據類型錯誤時
    """
    try:
        logger.info("開始調整入流數據時間間距")
        logger.info("輸入數據類型: %s", type(inflow_data))
        logger.info("目標時間間距: %s 小時", delta_t)

        # 1. 驗證並轉換輸入數據
        if inflow_data is None:
            raise ValueError("入流數據為空")

        # 如果是 list（從前端 JSON 傳來），轉換為 DataFrame
        if isinstance(inflow_data, list):
            if not inflow_data:
                raise ValueError("入流數據列表為空")

            # 檢查第一個元素的格式
            if not isinstance(inflow_data[0], dict):
                raise ValueError("入流數據格式錯誤，期望包含字典的列表")

            # 檢查必要的鍵
            required_keys = ['Time', 'Flow']
            missing_keys = [key for key in required_keys if key not in inflow_data[0]]
            if missing_keys:
                # 嘗試其他可能的鍵名
                first_item = inflow_data[0]
                key_mapping = {}

                # 時間相關的鍵名
                for key in first_item.keys():
                    key_lower = str(key).lower()
                    if 'time' in key_lower or 't' == key_lower or '時間' in key_lower:
                        key_mapping['Time'] = key
                    elif 'flow' in key_lower or 'q' == key_lower or '流量' in key_lower:
                        key_mapping['Flow'] = key

                # 重新映射數據
                if len(key_mapping) == 2:
                    logger.info("自動映射欄位: %s", key_mapping)
                    mapped_data = []
                    for item in inflow_data:
                        mapped_data.append({
                            'Time': item[key_mapping['Time']],
                            'Flow': item[key_mapping['Flow']]
                        })
                    inflow_df = pd.DataFrame(mapped_data)
                else:
                    raise ValueError(f"找不到必要的欄位，可用欄位: {list(inflow_data[0].keys())}")
            else:
                inflow_df = pd.DataFrame(inflow_data)

        elif isinstance(inflow_data, pd.DataFrame):
            inflow_df = inflow_data.copy()
        else:
            raise TypeError(f"不支援的數據類型: {type(inflow_data)}")

        # 2. 驗證 DataFrame 結構
        required_columns = ['Time', 'Flow']
        missing_columns = [col for col in required_columns if col not in inflow_df.columns]
        if missing_columns:
            raise ValueError(f"缺少必要欄位: {missing_columns}，現有欄位: {list(inflow_df.columns)}")

        # 3. 驗證並清理數據
        logger.info("原始數據形狀: %s", inflow_df.shape)

        # 移除空值
        initial_length = len(inflow_df)
        inflow_df = inflow_df.dropna(subset=['Time', 'Flow'])
        if len(inflow_df) < initial_length:
            logger.warning("移除了 %d 個包含空值的資料點", initial_length - len(inflow_df))

        if inflow_df.empty:
            raise ValueError("移除空值後數據為空")

        # 確保數據類型為數值
        try:
            inflow_df['Time'] = pd.to_numeric(inflow_df['Time'], errors='coerce')
            inflow_df['Flow'] = pd.to_numeric(inflow_df['Flow'], errors='coerce')

            # 再次移除轉換失敗的數據
            inflow_df = inflow_df.dropna()

            if inflow_df.empty:
                raise ValueError("數據轉換為數值後為空")

        except Exception as e:
            raise ValueError(f"數據類型轉換失敗: {str(e)}") from e

        # 4. 驗證 delta_t 參數
        if not isinstance(delta_t, (int, float)):
            raise TypeError("delta_t 必須是數值類型")

        if delta_t <= 0:
            raise ValueError("delta_t 必須大於 0")

        if delta_t > 24:  # 超過 24 小時可能不合理
            logger.warning("delta_t 值較大: %s 小時", delta_t)

        # 5. 數據預處理
        # 按時間排序
        inflow_df = inflow_df.sort_values('Time').reset_index(drop=True)
        logger.info("排序後數據形狀: %s", inflow_df.shape)

        # 移除重複的時間點（保留第一個）
        initial_length = len(inflow_df)
        inflow_df = inflow_df.drop_duplicates(subset=['Time'], keep='first')
        if len(inflow_df) < initial_length:
            logger.warning("移除了 %d 個重複的時間點", initial_length - len(inflow_df))

        # 檢查最少數據點要求
        if len(inflow_df) < 2:
            raise ValueError("數據點數量不足，至少需要 2 個有效數據點")

        # 6. 獲取時間範圍和統計資訊
        time_min = inflow_df['Time'].min()
        time_max = inflow_df['Time'].max()
        time_range = time_max - time_min
        original_interval = time_range / (len(inflow_df) - 1) if len(inflow_df) > 1 else delta_t

        logger.info("時間範圍: %.3f ~ %.3f 小時", time_min, time_max)
        logger.info("原始平均間距: %.3f 小時", original_interval)
        logger.info("目標間距: %.3f 小時", delta_t)

        # 7. 檢查間距合理性
        if delta_t > time_range:
            raise ValueError(f"時間間距 ({delta_t}) 大於數據總時間範圍 ({time_range:.3f})")

        # 8. 產生新的時間序列
        # 確保新時間序列的起點和終點與原始數據一致
        t_new = np.arange(time_min, time_max + delta_t/2, delta_t)  # 加入一半間距避免浮點數誤差

        # 確保最後一個時間點不超過原始最大值
        t_new = t_new[t_new <= time_max + 1e-10]  # 加入小誤差容忍

        logger.info("新時間序列長度: %d", len(t_new))
        logger.info("新時間範圍: %.3f ~ %.3f", t_new.min(), t_new.max())

        # 9. 執行插值
        try:
            # 使用 scipy 的 interp1d 進行線性插值
            interp_func = interp1d(
                inflow_df['Time'],
                inflow_df['Flow'],
                kind='linear',
                bounds_error=False,
                fill_value='extrapolate'
            )

            Q_new = interp_func(t_new)

            # 檢查插值結果
            if np.any(np.isnan(Q_new)):
                nan_count = np.sum(np.isnan(Q_new))
                logger.warning("插值結果包含 %d 個 NaN 值", nan_count)

                # 移除 NaN 值
                valid_mask = ~np.isnan(Q_new)
                t_new = t_new[valid_mask]
                Q_new = Q_new[valid_mask]

            if len(t_new) == 0:
                raise ValueError("插值後沒有有效數據點")

        except Exception as e:
            logger.error("插值失敗: %s", str(e))
            raise ValueError(f"數據插值失敗: {str(e)}") from e

        # 10. 組成新的 DataFrame
        adjusted_data = pd.DataFrame({
            'Time': t_new,
            'Flow': Q_new
        })

        # 11. 後處理和驗證
        # 確保流量值非負（如果需要）
        negative_flows = (adjusted_data['Flow'] < 0).sum()
        if negative_flows > 0:
            logger.warning("調整後數據包含 %d 個負流量值", negative_flows)
            # 可選：將負值設為 0
            # adjusted_data.loc[adjusted_data['Flow'] < 0, 'Flow'] = 0

        # 12. 統計資訊
        logger.info("=== 調整結果統計 ===")
        logger.info("原始數據點數: %d", len(inflow_df))
        logger.info("調整後數據點數: %d", len(adjusted_data))
        logger.info("原始流量範圍: %.3f ~ %.3f", inflow_df['Flow'].min(), inflow_df['Flow'].max())
        logger.info("調整後流量範圍: %.3f ~ %.3f", adjusted_data['Flow'].min(), adjusted_data['Flow'].max())
        logger.info("原始平均流量: %.3f", inflow_df['Flow'].mean())
        logger.info("調整後平均流量: %.3f", adjusted_data['Flow'].mean())

        # 13. 最終驗證
        if adjusted_data.empty:
            raise ValueError("調整後數據為空")

        if len(adjusted_data) < 2:
            raise ValueError("調整後數據點數量不足")

        logger.info("入流數據時間間距調整完成")
        return adjusted_data

    except (ValueError, TypeError, ImportError) as e:
        logger.error("入流數據調整失敗: %s", str(e))
        raise
    except Exception as e:
        logger.error("入流數據調整遇到未預期錯誤: %s", str(e))
        raise ValueError(f"數據調整失敗: {str(e)}") from e


def get_inflow_adjustment_summary(original_data, adjusted_data, delta_t):
    """
    獲取入流數據調整的摘要統計

    Args:
        original_data: pandas DataFrame，原始數據
        adjusted_data: pandas DataFrame，調整後數據
        delta_t: float，時間間距

    Returns:
        dict: 包含調整摘要的字典
    """
    try:
        summary = {
            'adjustment_info': {
                'target_interval': delta_t,
                'original_points': len(original_data),
                'adjusted_points': len(adjusted_data),
                'interpolation_method': 'Linear'
            },
            'time_statistics': {
                'original_range': {
                    'min': float(original_data['Time'].min()),
                    'max': float(original_data['Time'].max()),
                    'span': float(original_data['Time'].max() - original_data['Time'].min())
                },
                'adjusted_range': {
                    'min': float(adjusted_data['Time'].min()),
                    'max': float(adjusted_data['Time'].max()),
                    'span': float(adjusted_data['Time'].max() - adjusted_data['Time'].min())
                },
                'average_original_interval': float(
                    (original_data['Time'].max() - original_data['Time'].min()) /
                    (len(original_data) - 1)
                )
            },
            'flow_statistics': {
                'original': {
                    'min': float(original_data['Flow'].min()),
                    'max': float(original_data['Flow'].max()),
                    'mean': float(original_data['Flow'].mean()),
                    'std': float(original_data['Flow'].std())
                },
                'adjusted': {
                    'min': float(adjusted_data['Flow'].min()),
                    'max': float(adjusted_data['Flow'].max()),
                    'mean': float(adjusted_data['Flow'].mean()),
                    'std': float(adjusted_data['Flow'].std())
                }
            }
        }

        return summary

    except ValueError as e:
        logger.error("生成調整摘要失敗: %s", str(e))
        return {}


def generate_inflow_chart(inflow_data):
    """
    生成 入流流量歷線圖表
    Args:
        inflow_data: pandas DataFrame，包含時間和流量數據
    Returns:
        io.BytesIO: 圖片的二進制數據緩衝區，如果失敗則返回 None
    """
    try:
        t = inflow_data["Time"]
        Q = inflow_data["Flow"]
        idx_max = inflow_data['Flow'].idxmax()
        t_max = inflow_data.at[idx_max, 'Time']
        Q_max = inflow_data.at[idx_max, 'Flow']

        logger.info("開始繪製入流歷線圖表，數據點數: %d", len(Q))

        # 設定中文字體
        plt.rcParams["font.sans-serif"] = [
            "Microsoft JhengHei",
            "SimHei",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.set_facecolor('white')

        p1, = ax1.plot(t, Q, color="#1B1A57", linewidth=3)
        ax1.set_xlabel('歷時 (hr)',  fontsize=12)
        ax1.tick_params(axis='x')
        ax1.set_ylabel('流量 (cms)', fontsize=12)

        # 使用 auto_locator 自動設定刻度
        t_major, t_minor = auto_locator(t.min(), t.max())
        q_major, q_minor = auto_locator(Q.min(), Q.max())

        ax1.xaxis.set_major_locator(MultipleLocator(t_major))
        ax1.xaxis.set_minor_locator(MultipleLocator(t_minor))
        ax1.yaxis.set_major_locator(MultipleLocator(q_major))
        ax1.yaxis.set_minor_locator(MultipleLocator(q_minor))

        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax1.set_ylim(bottom=0)
        ax1.set_xlim(left=0)
        ax1.grid(True, which='major', axis='x', linestyle='-', linewidth=1, color='black', alpha=0.5)
        ax1.grid(True, which='major', axis='y', linestyle='-', linewidth=1, color='black', alpha=0.5)
        ax1.grid(True, which='minor', axis='y', linestyle='--', linewidth=0.5, color='black', alpha=0.5)

        ax1.annotate(
            f'$Q_{{p}}$ = {Q_max:,.2f} cms',
            xy=(t_max, Q_max), xytext=(t_max+10, Q_max-100),
            arrowprops=dict(arrowstyle='->', color="#1B1A57"),
            color='#1B1A57', fontsize=12,
            bbox=dict(boxstyle='round,pad=0.5', fc="#FFFFFF", ec="#1B1A57", alpha=1)
        )

        lines = [p1]
        labels = ['入流流量歷線']
        ax1.legend(lines, labels, loc='upper right', frameon=True, fontsize=12, fancybox=True, framealpha=1)

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

        logger.info("入流歷線圖表生成成功")
        return buffer

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("入流歷線圖表生成失敗: %s", e)
        if "fig" in locals():
            plt.close(fig)
        return None
