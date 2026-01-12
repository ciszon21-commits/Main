"""排洪演算平台視圖模組"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime
import logging
import traceback

# 匯入處理模組
from .modules.fd_step1_HAV import process_HAV_upload, generate_hav_chart
from .modules.fd_step2_inflow import (
    process_inflow_upload,
    validate_inflow_data,
    adjust_inflow_upload,
    get_inflow_adjustment_summary,
    generate_inflow_chart,
)
from .modules.fd_step3_fd import (
    process_drainage_upload,
    validate_drainage_data,
    generate_drainage_chart,
)
from .modules.fd_step5_calculation import (
    run_flood_calculation,
    run_flood_calculation_simple,
    generate_final_chart
)

# 全局變量來儲存處理後的數據
processed_data = {}

# 設定日誌記錄
logger = logging.getLogger(__name__)


def flood_drainage_app(request):
    """排洪演算主應用頁面 - 包含五個步驟的分頁介面"""
    initial_step = request.GET.get("step", "1")

    context = {
        "title": "排洪演算模組",
        "initial_step": initial_step,
        "steps": [
            {
                "id": 1,
                "name": "水庫庫容",
                "icon": "bi-water",
                "desc": "水位-面積-容量關係曲線",
            },
            {
                "id": 2,
                "name": "入流流量歷線",
                "icon": "bi-cloud-drizzle",
                "desc": "入流資料匯入與時距調整",
            },
            {
                "id": 3,
                "name": "排洪率定曲線",
                "icon": "bi-tsunami",
                "desc": "不同設施開度之排洪率定",
            },
            {
                "id": 4,
                "name": "排洪規則設定",
                "icon": "bi-gear",
                "desc": "各設施開關條件與開度控制",
            },
            {
                "id": 5,
                "name": "最終輸出",
                "icon": "bi-graph-up",
                "desc": "排洪演算與流量水位作圖",
            },
        ],
    }
    return render(request, "flood_drainage/fd_app.html", context)


# ==================== API 端點 ====================


@csrf_exempt
def api_upload(request):
    """API - 處理檔案上傳"""
    try:
        # 檢查是否有檔案上傳
        if "file" not in request.FILES:
            return JsonResponse({"success": False, "message": "沒有檔案被上傳"})

        uploaded_file = request.FILES["file"]
        step = int(request.POST.get("step", 1))

        logger.info("接收檔案上傳請求，步驟: %s，檔案名: %s", step, uploaded_file.name)

        if step == 1:
            # 步驟1: HAV數據處理
            hav_dataframe = process_HAV_upload(uploaded_file)

            if hav_dataframe is None:
                return JsonResponse(
                    {"success": False, "message": "HAV數據處理失敗，請檢查檔案格式"}
                )

            # 儲存到全局變數
            data_key = "step_%s" % step
            processed_data[data_key] = hav_dataframe

            # 轉換為前端需要的格式
            data_for_frontend = []
            for index, row in hav_dataframe.iterrows():
                data_for_frontend.append(
                    {
                        "level": float(row["H"]),
                        "area": float(row["A"]),
                        "volume": float(row["V"]),
                    }
                )

            logger.info("HAV數據處理成功，數據筆數: %d", len(data_for_frontend))

            return JsonResponse(
                {
                    "success": True,
                    "data": data_for_frontend,
                    "message": "檔案上傳成功！共處理 %d 筆數據"
                    % len(data_for_frontend),
                }
            )

        elif step == 2:
            # 步驟2: 入流流量歷線處理
            inflow_data, initial_wl = process_inflow_upload(uploaded_file)

            if inflow_data is None or initial_wl is None:
                return JsonResponse(
                    {"success": False, "message": "入流數據處理失敗，請檢查檔案格式"}
                )

            # 驗證數據
            is_valid, error_messages = validate_inflow_data(inflow_data, initial_wl)
            if not is_valid:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "數據驗證失敗: %s" % "; ".join(error_messages),
                    }
                )

            # 儲存到全局變數
            data_key = "step_%s" % step
            processed_data[data_key] = {
                "inflow_data": inflow_data,
                "initial_wl": initial_wl,
            }

            # 轉換為前端需要的格式
            data_for_frontend = []
            for index, row in inflow_data.iterrows():
                data_for_frontend.append(
                    {"Time": float(row["Time"]), "Flow": float(row["Flow"])}
                )

            logger.info(
                "入流數據處理成功，數據筆數: %d，初始水位: %s",
                len(data_for_frontend),
                initial_wl,
            )

            return JsonResponse(
                {
                    "success": True,
                    "data": data_for_frontend,
                    "initial_wl": initial_wl,
                    "message": "檔案上傳成功！共處理 %d 筆數據，初始水位: %sm"
                    % (len(data_for_frontend), initial_wl),
                }
            )

        elif step == 3:
            # 步驟3: 排洪率定曲線處理
            try:
                # 處理排洪設施數據上傳
                drainage_data, q_power, q_start, q_end = process_drainage_upload(
                    uploaded_file
                )

                if drainage_data is not None:
                    # 驗證數據
                    is_valid, error_messages = validate_drainage_data(drainage_data)

                    if is_valid:
                        # 保存數據到 processed_data
                        processed_data["step_3"] = drainage_data

                        logger.info("✅ 步驟3數據已保存到 processed_data")
                        logger.info("✅ 設施數量: %d", len(drainage_data["facilities"]))

                        return JsonResponse(
                            {
                                "success": True,
                                "message": (
                                    f'排洪設施數據上傳成功！共 {drainage_data["total_facilities"]} 個設施<br>'
                                    f"q_power: {q_power}, q_start: {q_start}, q_end: {q_end}"
                                ),
                                "data": drainage_data,
                                "count": drainage_data["total_facilities"],
                                "q_power": q_power,
                                "q_start": q_start,
                                "q_end": q_end,
                            }
                        )
                    else:
                        return JsonResponse(
                            {
                                "success": False,
                                "message": "排洪設施數據驗證失敗："
                                + "; ".join(error_messages),
                            }
                        )
                else:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "排洪設施數據處理失敗，請檢查檔案格式",
                        }
                    )

            except ImportError as import_error:
                logger.error("步驟3模組匯入失敗: %s", import_error)
                return JsonResponse(
                    {"success": False, "message": "步驟3處理模組載入失敗"}
                )

        else:
            return JsonResponse(
                {"success": False, "message": "步驟 %s 尚未支援" % step}
            )

    except ValueError as e:
        logger.error("數據處理錯誤: %s", e)
        return JsonResponse({"success": False, "message": str(e)})

    except (IOError, KeyError, TypeError) as e:
        logger.error("檔案上傳處理失敗: %s", e)
        return JsonResponse({"success": False, "message": "檔案處理失敗: %s" % str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_save(request):
    """API - 下載處理後的數據"""
    try:
        # 詳細的除錯日誌
        logger.info("=== API Save 請求開始 ===")
        logger.info("Request method: %s", request.method)
        logger.info("Request content_type: %s", request.content_type)
        logger.info("Request body: %s", request.body.decode("utf-8"))

        # 檢查 processed_data 的完整狀態
        logger.info("processed_data 鍵: %s", list(processed_data.keys()))
        logger.info("processed_data 完整內容:")
        for key, value in processed_data.items():
            if isinstance(value, dict):
                logger.info("  %s: dict with keys %s", key, list(value.keys()))
                for sub_key, sub_value in value.items():
                    logger.info(
                        "    %s: %s - %s...",
                        sub_key,
                        type(sub_value),
                        str(sub_value)[:100],
                    )
            else:
                logger.info("  %s: %s - %s...", key, type(value), str(value)[:100])

        # 解析請求參數
        body = json.loads(request.body)
        step = str(body.get("step"))
        data_type = body.get("type", "original")
        logger.info("解析參數: step=%s, type=%s", step, data_type)

        if not step:
            logger.error("步驟編號缺失")
            return JsonResponse({"success": False, "message": "請指定步驟編號"})

        # 步驟4是直接接收前端傳來的設定資料，沒有上傳步驟因此要先新增到processed_data
        if step == "4":
            # 儲存
            step4_data = body.get("data")
            if not step4_data or not isinstance(step4_data, list):
                return JsonResponse({"success": False, "message": "步驟4資料格式錯誤"})
            processed_data["step_4"] = step4_data
            logger.info("步驟4資料已儲存，共 %d 筆", len(step4_data))
            # 若為下載請求（type=download），則產生 Excel
            if data_type == "download":
                return handle_step4_download(step4_data)
            return JsonResponse({"success": True, "message": "步驟4資料已儲存"})

        # 檢查是否有先上傳該步驟的數據
        data_key = "step_%s" % step
        if data_key not in processed_data:
            logger.error("找不到步驟 %s 的數據", step)
            logger.error("可用的數據鍵: %s", list(processed_data.keys()))
            return JsonResponse(
                {
                    "success": False,
                    "message": "步驟 %s 沒有可下載的數據，請先上傳檔案。可用數據: %s"
                    % (step, list(processed_data.keys())),
                }
            )

        step_data = processed_data[data_key]
        logger.info("找到步驟 %s 數據，類型: %s", step, type(step_data))

        # 根據步驟處理不同的下載邏輯
        if step == "1":
            logger.info("處理步驟1下載")
            return handle_step1_download(step_data, data_type)

        elif step == "2":
            logger.info("處理步驟2下載")
            return handle_step2_download(step_data, data_type)

        elif step == "3":
            logger.info("處理步驟3下載")
            return handle_step3_download(step_data, data_type)

        elif step == "5":
            # 取得 processed_data["step_5"]
            step5_data = processed_data.get("step_5")
            if step5_data is None:
                return JsonResponse({"success": False, "message": "尚未執行排洪演算，無法下載"})

            # 檢查型態
            if not isinstance(step5_data, pd.DataFrame):
                return JsonResponse({"success": False, "message": "步驟5數據格式錯誤（非DataFrame）"})

            # 檢查是否有資料
            if step5_data.empty:
                return JsonResponse({"success": False, "message": "步驟5數據為空，無法下載"})

            # 檢查必要欄位
            required_cols = ["時間(hr)", "流量(cms)", "總出流量(cms)", "水庫水位(m)"]
            missing_cols = [col for col in required_cols if col not in step5_data.columns]
            if missing_cols:
                return JsonResponse({
                    "success": False,
                    "message": f"步驟5數據缺少必要欄位: {missing_cols}，現有欄位: {list(step5_data.columns)}"
                })

            # 產生 Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                step5_data.to_excel(writer, index=False, sheet_name="排洪演算結果")
            output.seek(0)
            excel_content = output.read()
            if len(excel_content) == 0:
                return JsonResponse({"success": False, "message": "產生的Excel檔案為空"})

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"最終輸出_排洪演算結果_{timestamp}.xlsx"
            response = HttpResponse(
                excel_content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = len(excel_content)
            return response

        else:
            logger.error("不支援的步驟: %s", step)
            return JsonResponse(
                {"success": False, "message": "步驟 %s 的下載功能尚未實現" % step}
            )

    except json.JSONDecodeError as e:
        logger.error("JSON 解析失敗: %s", str(e))
        return JsonResponse({"success": False, "message": "請求格式錯誤: %s" % str(e)})

    except Exception as e:
        logger.error("下載處理失敗: %s", str(e), exc_info=True)
        return JsonResponse(
            {"success": False, "message": "下載檔案時發生錯誤: %s" % str(e)}
        )


@csrf_exempt
@require_http_methods(["POST"])
def api_adjust_inflow(request):
    """API - 調整入流數據的時間間距"""
    try:
        logger.info("=== API 調整入流數據請求開始 ===")

        # 解析請求參數
        body = json.loads(request.body)
        step = str(body.get("step", "2"))  # 預設為步驟2
        delta_t = body.get("delta_t")

        logger.info("調整參數: step=%s, delta_t=%s", step, delta_t)

        # 驗證參數
        if not delta_t:
            return JsonResponse({"success": False, "message": "請指定時間間距 delta_t"})

        try:
            delta_t = float(delta_t)
        except (ValueError, TypeError):
            return JsonResponse({"success": False, "message": "時間間距必須是數值"})

        if delta_t <= 0:
            return JsonResponse({"success": False, "message": "時間間距必須大於 0"})

        # 檢查是否有原始數據
        data_key = "step_%s" % step
        if data_key not in processed_data:
            return JsonResponse(
                {"success": False, "message": "沒有找到原始入流數據，請先上傳檔案"}
            )

        step_data = processed_data[data_key]

        # 檢查數據結構
        if not isinstance(step_data, dict) or "inflow_data" not in step_data:
            return JsonResponse({"success": False, "message": "原始數據格式錯誤"})

        original_inflow_data = step_data["inflow_data"]
        initial_wl = step_data.get("initial_wl")

        logger.info("原始數據形狀: %s", original_inflow_data.shape)
        logger.info("調整時間間距: %s 小時", delta_t)

        # 調用調整函數
        try:
            adjusted_data = adjust_inflow_upload(original_inflow_data, delta_t)
            logger.info("調整後數據形狀: %s", adjusted_data.shape)

        except Exception as adjust_error:
            logger.error("數據調整失敗: %s", str(adjust_error))
            return JsonResponse(
                {"success": False, "message": "數據調整失敗: %s" % str(adjust_error)}
            )

        # 生成調整摘要
        try:
            adjustment_summary = get_inflow_adjustment_summary(
                original_inflow_data, adjusted_data, delta_t
            )
        except Exception as summary_error:
            logger.warning("生成調整摘要失敗: %s", str(summary_error))
            adjustment_summary = {}

        # 儲存調整後的數據到全局變數
        processed_data[data_key]["adjusted_data"] = adjusted_data
        processed_data[data_key]["delta_t"] = delta_t
        processed_data[data_key]["adjustment_summary"] = adjustment_summary

        # 轉換為前端需要的格式
        adjusted_data_for_frontend = []
        for index, row in adjusted_data.iterrows():
            adjusted_data_for_frontend.append(
                {"Time": float(row["Time"]), "Flow": float(row["Flow"])}
            )

        logger.info("入流數據調整成功")

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "adjusted_data": adjusted_data_for_frontend,
                    "original_count": len(original_inflow_data),
                    "adjusted_count": len(adjusted_data),
                    "delta_t": delta_t,
                    "initial_wl": initial_wl,
                    "summary": adjustment_summary,
                },
                "message": "時間間距調整成功！原始 %d 筆 → 調整後 %d 筆 (Δt = %s 小時)"
                % (len(original_inflow_data), len(adjusted_data), delta_t),
            }
        )

    except json.JSONDecodeError as e:
        logger.error("JSON 解析失敗: %s", str(e))
        return JsonResponse({"success": False, "message": "請求格式錯誤: %s" % str(e)})

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("調整處理失敗: %s", str(e), exc_info=True)
        return JsonResponse(
            {"success": False, "message": "數據調整時發生錯誤: %s" % str(e)}
        )


@csrf_exempt
@require_http_methods(["GET"])
def api_get_adjustment_info(request):
    """API - 獲取調整數據的詳細資訊"""
    try:
        step = request.GET.get("step", "2")
        data_key = "step_%s" % step

        if data_key not in processed_data:
            return JsonResponse({"success": False, "message": "沒有找到數據"})

        step_data = processed_data[data_key]

        # 檢查是否有調整後的數據
        if "adjusted_data" not in step_data:
            return JsonResponse({"success": False, "message": "沒有找到調整後的數據"})

        # 準備返回的資訊
        info = {
            "has_original": "inflow_data" in step_data,
            "has_adjusted": "adjusted_data" in step_data,
            "original_count": (
                len(step_data["inflow_data"]) if "inflow_data" in step_data else 0
            ),
            "adjusted_count": (
                len(step_data["adjusted_data"]) if "adjusted_data" in step_data else 0
            ),
            "delta_t": step_data.get("delta_t"),
            "initial_wl": step_data.get("initial_wl"),
            "adjustment_summary": step_data.get("adjustment_summary", {}),
        }

        return JsonResponse({"success": True, "info": info})

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("獲取調整資訊失敗: %s", str(e))
        return JsonResponse(
            {"success": False, "message": "獲取調整資訊失敗: %s" % str(e)}
        )


@csrf_exempt
@require_http_methods(["POST"])
def api_run_flood_calculation(request):
    """
    API - 執行完整版排洪演算（支援步驟四控制條件）
    前端需先完成步驟1~4的資料上傳
    """
    try:
        body = json.loads(request.body)
        q_start = float(body.get("q_start", 0))
        q_power = float(body.get("q_power", 0))
        q_end = float(body.get("q_end", 0))

        # 取得步驟1~4資料
        hav_df = processed_data.get("step_1")
        inflow_info = processed_data.get("step_2")
        fd_info = processed_data.get("step_3")
        step4_controls = processed_data.get("step_4")

        if hav_df is None or inflow_info is None or fd_info is None or step4_controls is None:
            return JsonResponse({
                "success": False,
                "message": "請先完成步驟1~4資料上傳"
            })

        # 解析 HAV
        if isinstance(hav_df, pd.DataFrame):
            H_arr = hav_df["H"].values if "H" in hav_df.columns else hav_df["水位"].values
            V_arr = hav_df["V"].values if "V" in hav_df.columns else hav_df["容量"].values
        else:
            return JsonResponse({"success": False, "message": "HAV資料格式錯誤"})

        # 解析 inflow
        inflow_data = inflow_info.get("adjusted_data") if "adjusted_data" in inflow_info else inflow_info.get("inflow_data")
        initial_wl = inflow_info.get("initial_wl")
        if inflow_data is None or initial_wl is None:
            return JsonResponse({"success": False, "message": "入流資料格式錯誤"})

        # 解析設施
        structure_infos = fd_info.get("facilities") if isinstance(fd_info, dict) else fd_info
        if not structure_infos:
            return JsonResponse({"success": False, "message": "排洪設施資料格式錯誤"})

        # 解析步驟四控制條件（確保是list of dicts）
        if not isinstance(step4_controls, list):
            return JsonResponse({"success": False, "message": "步驟四控制條件格式錯誤"})
        # 若前端傳來的是dict包data，則取data
        if len(step4_controls) > 0 and isinstance(step4_controls[0], dict) and "facility" not in step4_controls[0]:
            step4_controls = step4_controls[0].get("data", [])

        # 執行主計算
        result_df = run_flood_calculation(
            inflow_data=inflow_data,
            initial_wl=float(initial_wl),
            H_arr=np.array(H_arr, dtype=float),
            V_arr=np.array(V_arr, dtype=float),
            structure_infos=structure_infos,
            q_start=q_start,
            q_power=q_power,
            q_end=q_end,
            step4_controls=step4_controls
        )

        # 儲存結果到 processed_data
        processed_data["step_5"] = result_df

        # 回傳前端需要的格式
        data_for_frontend = result_df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict(orient="records")
        return JsonResponse({
            "success": True,
            "data": data_for_frontend,
            "columns": list(result_df.columns),
            "message": "排洪演算完成"
        })

    except Exception as e:
        logger.error("完整版排洪演算失敗: %s", str(e), exc_info=True)
        return JsonResponse({
            "success": False,
            "message": f"排洪演算失敗: {e}",
            "trace": traceback.format_exc()
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_run_flood_calculation_simple(request):
    """
    API - 執行簡易排洪演算
    前端需先完成步驟1~3的資料上傳
    """
    try:
        # 解析請求參數（可擴充，這裡假設用預設值）
        body = json.loads(request.body)
        q_start = float(body.get("q_start", 0))
        q_power = float(body.get("q_power", 0))
        q_end = float(body.get("q_end", 0))

        # 取得步驟1~3資料
        hav_df = processed_data.get("step_1")
        inflow_info = processed_data.get("step_2")
        fd_info = processed_data.get("step_3")

        if hav_df is None or inflow_info is None or fd_info is None:
            return JsonResponse({
                "success": False,
                "message": "請先完成步驟1~3的資料上傳"
            })

        # 解析 HAV
        if isinstance(hav_df, pd.DataFrame):
            H_arr = hav_df["H"].values if "H" in hav_df.columns else hav_df.iloc[:, 0].values
            V_arr = hav_df["V"].values if "V" in hav_df.columns else hav_df.iloc[:, 2].values
        else:
            return JsonResponse({"success": False, "message": "HAV資料格式錯誤"})

        # 解析 inflow
        inflow_data = inflow_info.get("adjusted_data") if "adjusted_data" in inflow_info else inflow_info.get("inflow_data")
        initial_wl = inflow_info.get("initial_wl")
        if inflow_data is None or initial_wl is None:
            return JsonResponse({"success": False, "message": "入流資料不完整"})

        # 解析設施
        structure_infos = fd_info.get("facilities") if isinstance(fd_info, dict) else fd_info
        if not structure_infos:
            return JsonResponse({"success": False, "message": "排洪設施資料不完整"})

        # 執行主計算
        result_df = run_flood_calculation_simple(
            inflow_data=inflow_data,
            initial_wl=float(initial_wl),
            H_arr=np.array(H_arr, dtype=float),
            V_arr=np.array(V_arr, dtype=float),
            structure_infos=structure_infos,
            q_start=q_start,
            q_power=q_power,
            q_end=q_end
        )

        # 儲存結果到 processed_data
        processed_data["step_5"] = result_df

        # 回傳前端需要的格式
        data_for_frontend = result_df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict(orient="records")
        return JsonResponse({
            "success": True,
            "data": data_for_frontend,
            "columns": list(result_df.columns),
            "message": "排洪演算完成"
        })

    except Exception as e:
        logger.error("排洪演算失敗: %s", str(e), exc_info=True)
        return JsonResponse({
            "success": False,
            "message": f"排洪演算失敗: {e}",
            "trace": traceback.format_exc()
        })


@csrf_exempt
@require_http_methods(["POST"])
def export_chart(request):
    """匯出圖表為圖片檔案"""
    try:
        step = int(request.POST.get("step", 1))
        logger.info("開始匯出步驟 %s 的圖表", step)

        # 🔧 詳細的除錯資訊
        logger.info("當前 processed_data 鍵值: %s", list(processed_data.keys()))

        # 檢查 processed_data 中是否有數據
        data_key = "step_%s" % step
        logger.info("尋找數據鍵值: %s", data_key)

        if data_key not in processed_data:
            logger.error(
                "找不到數據鍵值 %s，可用鍵值: %s", data_key, list(processed_data.keys())
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "沒有找到數據，請先上傳檔案。可用數據: %s"
                    % list(processed_data.keys()),
                }
            )

        # 取得數據
        step_data = processed_data[data_key]
        logger.info("步驟 %s 數據類型: %s", step, type(step_data))

        # 根據不同步驟調用對應的圖表生成函數
        if step == 1:
            # 步驟1的現有邏輯
            try:
                image_buffer = generate_hav_chart(step_data)

                if image_buffer is None:
                    logger.error("步驟1圖表生成失敗")
                    return JsonResponse({"success": False, "message": "圖表生成失敗"})

                # 檢查 buffer 內容
                image_content = image_buffer.getvalue()
                logger.info("圖表生成成功，大小: %d bytes", len(image_content))

                if len(image_content) == 0:
                    logger.error("生成的圖片內容為空")
                    return JsonResponse(
                        {"success": False, "message": "生成的圖片內容為空"}
                    )

                # 準備檔案下載
                filename = "HAV_關係圖_%s.png" % datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                # 建立 HTTP 響應
                response = HttpResponse(image_content, content_type="image/png")
                response["Content-Disposition"] = 'attachment; filename="%s"' % filename
                response["Content-Length"] = len(image_content)

                logger.info("成功匯出步驟 %s 圖表: %s", step, filename)
                return response

            except ImportError as import_error:
                logger.error("無法匯入圖表生成函數: %s", str(import_error))
                return JsonResponse(
                    {"success": False, "message": "圖表生成模組載入失敗"}
                )
            except RuntimeError as chart_error:
                logger.error("步驟1圖表生成錯誤: %s", str(chart_error), exc_info=True)
                return JsonResponse(
                    {"success": False, "message": "圖表生成失敗: %s" % str(chart_error)}
                )

        elif step == 2:
            # 🔧 步驟2的圖表匯出邏輯
            try:
                logger.info("步驟2數據內容: %s", step_data)

                # 優先使用調整後數據，如果沒有則使用原始數據
                if (
                    "adjusted_data" in step_data
                    and step_data["adjusted_data"] is not None
                ):
                    chart_data = step_data["adjusted_data"]
                    logger.info("使用調整後數據繪圖，數據筆數: %d", len(chart_data))
                elif (
                    "inflow_data" in step_data and step_data["inflow_data"] is not None
                ):
                    chart_data = step_data["inflow_data"]
                    logger.info("使用原始數據繪圖，數據筆數: %d", len(chart_data))
                else:
                    logger.error("步驟2沒有可用的入流數據")
                    return JsonResponse(
                        {"success": False, "message": "沒有可用的入流數據"}
                    )

                # 生成圖表
                image_buffer = generate_inflow_chart(chart_data)

                if image_buffer is None:
                    logger.error("步驟2圖表生成失敗")
                    return JsonResponse(
                        {"success": False, "message": "入流數據圖表生成失敗"}
                    )

                # 檢查 buffer 內容
                image_content = image_buffer.getvalue()
                logger.info("步驟2圖表生成成功，大小: %d bytes", len(image_content))

                if len(image_content) == 0:
                    logger.error("生成的圖片內容為空")
                    return JsonResponse(
                        {"success": False, "message": "生成的圖片內容為空"}
                    )

                # 準備檔案下載
                data_type = (
                    "調整後"
                    if "adjusted_data" in step_data
                    and step_data["adjusted_data"] is not None
                    else "原始"
                )
                filename = f"入流流量歷線圖_{data_type}數據_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                # 建立 HTTP 響應
                response = HttpResponse(image_content, content_type="image/png")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                response["Content-Length"] = len(image_content)

                logger.info("成功匯出步驟 %s 圖表: %s", step, filename)
                return response

            except ImportError as import_error:
                logger.error("無法匯入步驟2圖表生成函數: %s", str(import_error))
                return JsonResponse(
                    {"success": False, "message": "步驟2圖表生成模組載入失敗"}
                )
            except RuntimeError as chart_error:
                logger.error("步驟2圖表生成錯誤: %s", str(chart_error), exc_info=True)
                return JsonResponse(
                    {
                        "success": False,
                        "message": "步驟2圖表生成失敗: %s" % str(chart_error),
                    }
                )

        elif step == 3:
            try:
                logger.info("步驟3數據內容: %s", step_data)

                # 檢查數據格式
                if "facilities" not in step_data:
                    logger.error("步驟3沒有設施數據")
                    return JsonResponse(
                        {"success": False, "message": "沒有可用的設施數據"}
                    )

                facilities = step_data["facilities"]
                if not facilities or len(facilities) == 0:
                    logger.error("步驟3設施數據為空")
                    return JsonResponse({"success": False, "message": "設施數據為空"})

                # 🔧 修復：獲取當前選中的設施ID（從請求中）
                facility_id = request.POST.get("facility_id")
                logger.info("接收到的設施ID參數: %s", facility_id)

                if facility_id:
                    try:
                        facility_id = int(facility_id)
                        logger.info("解析設施ID: %d", facility_id)

                        # 查找指定設施
                        current_facility = next(
                            (f for f in facilities if f["id"] == facility_id), None
                        )
                        if not current_facility:
                            logger.error("找不到指定的設施ID: %d", facility_id)
                            logger.info(
                                "可用的設施: %s",
                                [(f["id"], f["name"]) for f in facilities],
                            )
                            return JsonResponse(
                                {
                                    "success": False,
                                    "message": f"找不到指定的設施 (ID: {facility_id})",
                                }
                            )
                        logger.info(
                            "找到指定設施: %s (ID: %d)",
                            current_facility["name"],
                            facility_id,
                        )

                    except (ValueError, TypeError) as parse_error:
                        logger.error(
                            "設施ID解析失敗: %s -> %s", facility_id, str(parse_error)
                        )
                        return JsonResponse(
                            {
                                "success": False,
                                "message": f"無效的設施ID: {facility_id}",
                            }
                        )
                else:
                    # 🔧 修復：如果沒有指定設施ID，使用第一個設施並記錄警告
                    current_facility = facilities[0]
                    logger.warning(
                        "沒有指定設施ID，使用第一個設施: %s (ID: %d)",
                        current_facility["name"],
                        current_facility["id"],
                    )

                logger.info("為設施 '%s' 生成圖表", current_facility["name"])

                # 生成圖表
                image_buffer = generate_drainage_chart(current_facility)

                if image_buffer is None:
                    logger.error("步驟3圖表生成失敗")
                    return JsonResponse(
                        {"success": False, "message": "排洪率定曲線圖表生成失敗"}
                    )

                # 檢查 buffer 內容
                image_content = image_buffer.getvalue()
                logger.info("步驟3圖表生成成功，大小: %d bytes", len(image_content))

                if len(image_content) == 0:
                    logger.error("生成的圖片內容為空")
                    return JsonResponse(
                        {"success": False, "message": "生成的圖片內容為空"}
                    )

                # 準備檔案下載
                facility_name = current_facility["name"]
                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )  # 🔧 修復：統一時間格式
                filename = f"步驟3_排洪率定曲線_{facility_name}_{timestamp}.png"

                # 建立 HTTP 響應
                response = HttpResponse(image_content, content_type="image/png")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                response["Content-Length"] = len(image_content)

                logger.info("成功匯出步驟 %s 圖表: %s", step, filename)
                return response

            except ImportError as import_error:
                logger.error("無法匯入步驟3圖表生成函數: %s", str(import_error))
                return JsonResponse(
                    {"success": False, "message": "步驟3圖表生成模組載入失敗"}
                )
            except Exception as chart_error:
                logger.error("步驟3圖表生成錯誤: %s", str(chart_error), exc_info=True)
                return JsonResponse(
                    {
                        "success": False,
                        "message": "步驟3圖表生成失敗: %s" % str(chart_error),
                    }
                )

        elif step == 5:
            # 匯出最終演算圖
            df = step_data  # 預設已是 DataFrame
            buf = generate_final_chart(df)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"最終輸出_排洪演算結果圖_{timestamp}.png"
            response = HttpResponse(
                buf.getvalue(),
                content_type="image/png"
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = buf.getbuffer().nbytes
            return response

        else:
            return JsonResponse(
                {"success": False, "message": "步驟 %s 尚未支援圖表匯出" % step}
            )

    except ValueError as e:
        logger.error("步驟參數錯誤: %s", e)
        return JsonResponse({"success": False, "message": "無效的步驟參數"})
    except Exception as e:
        logger.error("圖表匯出失敗: %s", e, exc_info=True)
        return JsonResponse({"success": False, "message": "圖表匯出失敗: %s" % str(e)})


# ==================== 處理函數 ====================


def handle_step1_download(hav_data, data_type):
    """處理步驟1的數據下載"""
    try:
        logger.info("=== 處理步驟1下載 ===")
        logger.info("數據類型: %s", type(hav_data))
        logger.info("數據內容: %s...", str(hav_data)[:200])

        # 如果數據是 DataFrame，直接使用
        if isinstance(hav_data, pd.DataFrame):
            df = hav_data
            logger.info(
                "直接使用 DataFrame，形狀: %s, 欄位: %s", df.shape, list(df.columns)
            )

        # 如果數據是字典列表（從前端上傳的格式）
        elif (
            isinstance(hav_data, list)
            and len(hav_data) > 0
            and isinstance(hav_data[0], dict)
        ):
            df = pd.DataFrame(hav_data)
            logger.info(
                "從字典列表創建 DataFrame，形狀: %s, 欄位: %s",
                df.shape,
                list(df.columns),
            )

        # 如果數據是單個字典
        elif isinstance(hav_data, dict):
            # 可能需要進一步處理
            logger.info("數據是字典，鍵: %s", list(hav_data.keys()))

            # 嘗試找到實際的數據
            for key, value in hav_data.items():
                if isinstance(value, (list, pd.DataFrame)):
                    if isinstance(value, list):
                        df = pd.DataFrame(value)
                    else:
                        df = value
                    logger.info("在鍵 '%s' 中找到數據，形狀: %s", key, df.shape)
                    break
            else:
                logger.error("在字典中找不到有效的數據")
                return JsonResponse(
                    {
                        "success": False,
                        "message": "步驟1數據格式不正確，字典鍵: %s"
                        % list(hav_data.keys()),
                    }
                )

        else:
            logger.error("不支援的數據格式: %s", type(hav_data))
            return JsonResponse(
                {"success": False, "message": "步驟1數據格式錯誤: %s" % type(hav_data)}
            )

        # 檢查 DataFrame 是否有數據
        if df.empty:
            logger.error("DataFrame 為空")
            return JsonResponse({"success": False, "message": "步驟1數據為空"})

        # 確保有正確的欄位
        logger.info("DataFrame 欄位: %s", list(df.columns))

        # 嘗試標準化欄位名稱
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if "level" in col_lower or "h" in col_lower or "水位" in col_lower:
                column_mapping[col] = "H"
            elif "area" in col_lower or "a" in col_lower or "面積" in col_lower:
                column_mapping[col] = "A"
            elif (
                "volume" in col_lower
                or "v" in col_lower
                or "容量" in col_lower
                or "capacity" in col_lower
            ):
                column_mapping[col] = "V"

        if column_mapping:
            df = df.rename(columns=column_mapping)
            logger.info("重新命名欄位: %s", column_mapping)
            logger.info("重新命名後的欄位: %s", list(df.columns))

        # 檢查必要欄位
        required_columns = ["H", "A", "V"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error("缺少必要欄位: %s", missing_columns)
            return JsonResponse(
                {
                    "success": False,
                    "message": "數據缺少必要欄位: %s，現有欄位: %s"
                    % (missing_columns, list(df.columns)),
                }
            )

        # 創建 Excel 檔案
        logger.info("開始創建 Excel 檔案")
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # 重新命名欄位為中文
            df_display = df[["H", "A", "V"]].copy()
            df_display.columns = ["水位(m)", "面積(m²)", "容量(m³)"]

            # 寫入數據
            df_display.to_excel(writer, sheet_name="水庫庫容數據", index=False)
            logger.info("寫入數據到 Excel，行數: %d", len(df_display))

            # 🔧 統一：添加統計資訊工作表
            try:
                stats_data = pd.DataFrame(
                    {
                        "項目": [
                            "數據類型",
                            "總記錄數",
                            "最小水位(m)",
                            "最大水位(m)",
                            "最小面積(m²)",
                            "最大面積(m²)",
                            "最小容量(m³)",
                            "最大容量(m³)",
                            "下載時間",
                        ],
                        "數值": [
                            "水庫庫容數據",
                            len(df),
                            round(df["H"].min(), 3),
                            round(df["H"].max(), 3),
                            round(df["A"].min(), 3),
                            round(df["A"].max(), 3),
                            round(df["V"].min(), 3),
                            round(df["V"].max(), 3),
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ],
                    }
                )
                stats_data.to_excel(writer, sheet_name="統計資訊", index=False)
                logger.info("添加統計資訊成功")
            except (ValueError, TypeError) as stats_error:
                logger.warning("添加統計資訊失敗: %s", str(stats_error))

        output.seek(0)
        excel_content = output.read()

        logger.info("Excel 檔案創建完成，大小: %d bytes", len(excel_content))

        if len(excel_content) == 0:
            logger.error("生成的 Excel 檔案為空")
            return JsonResponse({"success": False, "message": "生成的檔案為空"})

        # 🔧 統一：生成檔案名稱格式
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "步驟1_水庫庫容數據_%s.xlsx" % timestamp

        # 設定 HTTP 響應
        response = HttpResponse(
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response["Content-Length"] = len(excel_content)

        logger.info(
            "步驟1數據下載成功: %s, 大小: %d bytes", filename, len(excel_content)
        )
        return response

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("步驟1下載失敗: %s", str(e), exc_info=True)
        return JsonResponse({"success": False, "message": "步驟1下載失敗: %s" % str(e)})


def handle_step2_download(step2_data, data_type):
    """處理步驟2的數據下載 - 支援原始和調整後數據"""
    try:
        logger.info("處理步驟2下載: type=%s", data_type)
        logger.info("步驟2數據內容: %s", step2_data)

        # 檢查數據結構
        if not isinstance(step2_data, dict):
            logger.error("步驟2數據格式錯誤: %s", type(step2_data))
            return JsonResponse({"success": False, "message": "步驟2數據格式錯誤"})

        # 根據 data_type 選擇數據來源
        if data_type == "original":
            # 原始數據
            if "inflow_data" not in step2_data:
                logger.error("找不到 inflow_data，可用鍵: %s", list(step2_data.keys()))
                return JsonResponse(
                    {"success": False, "message": "沒有找到原始入流數據"}
                )

            target_data = step2_data["inflow_data"]
            sheet_name = "原始入流數據"
            type_name = "原始"

        elif data_type == "adjusted":
            # 調整後數據
            if "adjusted_data" not in step2_data:
                logger.error(
                    "找不到 adjusted_data，可用鍵: %s", list(step2_data.keys())
                )
                return JsonResponse(
                    {
                        "success": False,
                        "message": "沒有找到調整後的入流數據，請先執行時間間距調整",
                    }
                )

            target_data = step2_data["adjusted_data"]
            sheet_name = "調整後入流數據"
            type_name = "調整後"

        else:
            logger.error("無效的數據類型: %s", data_type)
            return JsonResponse(
                {"success": False, "message": "無效的數據類型: %s" % data_type}
            )

        initial_wl = step2_data.get("initial_wl", None)
        delta_t = step2_data.get("delta_t", None)
        adjustment_summary = step2_data.get("adjustment_summary", {})

        logger.info(
            "選擇的數據類型: %s, 形狀: %s",
            type(target_data),
            target_data.shape if hasattr(target_data, "shape") else "no shape",
        )

        # 創建 Excel 檔案
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # 重新命名欄位為中文
            target_data_display = target_data[["Time", "Flow"]].copy()
            target_data_display.columns = ["歷時(hr)", "流量(cms)"]

            # 寫入主要數據
            target_data_display.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info("寫入%s入流數據到 Excel", type_name)

            # 🔧 統一：添加統計資訊工作表
            try:
                stats_items = [
                    "數據類型",
                    "總記錄數",
                    "初始水位(m)",
                    "最小流量(cms)",
                    "最大流量(cms)",
                    "平均流量(cms)",
                    "總時間(hr)",
                    "下載時間",
                ]

                stats_values = [
                    f"{type_name}入流數據",
                    len(target_data),
                    initial_wl if initial_wl is not None else "未設定",
                    (
                        round(target_data["Flow"].min(), 3)
                        if "Flow" in target_data.columns
                        else "未知"
                    ),
                    (
                        round(target_data["Flow"].max(), 3)
                        if "Flow" in target_data.columns
                        else "未知"
                    ),
                    (
                        round(target_data["Flow"].mean(), 3)
                        if "Flow" in target_data.columns
                        else "未知"
                    ),
                    (
                        round(target_data["Time"].max(), 3)
                        if "Time" in target_data.columns
                        else "未知"
                    ),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]

                # 如果是調整後數據，添加額外資訊
                if data_type == "adjusted" and delta_t is not None:
                    stats_items.extend(["時間間距(hr)", "插值方法"])
                    stats_values.extend([delta_t, "線性插值"])

                stats_data = pd.DataFrame({"項目": stats_items, "數值": stats_values})
                stats_data.to_excel(writer, sheet_name="統計資訊", index=False)
                logger.info("添加統計資訊到 Excel")

                # 如果有調整摘要，添加調整詳細資訊
                if data_type == "adjusted" and adjustment_summary:
                    try:
                        summary_items = []
                        summary_values = []

                        # 調整資訊
                        if "adjustment_info" in adjustment_summary:
                            adj_info = adjustment_summary["adjustment_info"]
                            summary_items.extend(
                                [
                                    "目標時間間距",
                                    "原始數據點數",
                                    "調整後數據點數",
                                    "插值方法",
                                ]
                            )
                            summary_values.extend(
                                [
                                    adj_info.get("target_interval", "未知"),
                                    adj_info.get("original_points", "未知"),
                                    adj_info.get("adjusted_points", "未知"),
                                    adj_info.get("interpolation_method", "未知"),
                                ]
                            )

                        # 時間統計
                        if "time_statistics" in adjustment_summary:
                            time_stats = adjustment_summary["time_statistics"]
                            if "original_range" in time_stats:
                                orig_range = time_stats["original_range"]
                                summary_items.extend(
                                    ["原始時間範圍(hr)", "原始平均間距(hr)"]
                                )
                                summary_values.extend(
                                    [
                                        "%.3f ~ %.3f"
                                        % (
                                            orig_range.get("min", 0),
                                            orig_range.get("max", 0),
                                        ),
                                        "%.3f"
                                        % time_stats.get(
                                            "average_original_interval", 0
                                        ),
                                    ]
                                )

                        if summary_items:
                            adjustment_detail = pd.DataFrame(
                                {"調整項目": summary_items, "數值": summary_values}
                            )
                            adjustment_detail.to_excel(
                                writer, sheet_name="調整詳細資訊", index=False
                            )
                            logger.info("添加調整詳細資訊到 Excel")

                    except Exception as detail_error:
                        logger.warning("添加調整詳細資訊失敗: %s", str(detail_error))

            except Exception as stats_error:
                logger.warning("添加統計資訊失敗: %s", str(stats_error))

        output.seek(0)
        excel_content = output.read()

        logger.info("Excel 檔案大小: %d bytes", len(excel_content))

        # 🔧 統一：生成檔案名稱格式
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if data_type == "adjusted" and delta_t:
            filename = "步驟2_調整後入流數據_Δt%shr_%s.xlsx" % (delta_t, timestamp)
        else:
            filename = "步驟2_原始入流數據_%s.xlsx" % timestamp

        # 設定 HTTP 響應
        response = HttpResponse(
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response["Content-Length"] = len(excel_content)

        logger.info(
            "步驟2數據下載成功: %s, 大小: %d bytes", filename, len(excel_content)
        )
        return response

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("步驟2下載失敗: %s", str(e), exc_info=True)
        return JsonResponse({"success": False, "message": "步驟2下載失敗: %s" % str(e)})


def handle_step3_download(step3_data, data_type):
    """處理步驟3的數據下載 - 排洪設施數據"""
    try:
        logger.info("處理步驟3下載: type=%s", data_type)
        logger.info("步驟3數據內容: %s", step3_data)

        # 檢查數據結構
        if not isinstance(step3_data, dict):
            logger.error("步驟3數據格式錯誤: %s", type(step3_data))
            return JsonResponse({"success": False, "message": "步驟3數據格式錯誤"})

        # 檢查是否有設施數據
        if "facilities" not in step3_data:
            logger.error("找不到 facilities 數據，可用鍵: %s", list(step3_data.keys()))
            return JsonResponse({"success": False, "message": "沒有找到排洪設施數據"})

        facilities = step3_data["facilities"]
        if not facilities or len(facilities) == 0:
            logger.error("設施數據為空")
            return JsonResponse({"success": False, "message": "排洪設施數據為空"})

        logger.info("處理 %d 個設施的數據", len(facilities))

        # 創建 Excel 檔案
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            # 為每個設施創建一個工作表
            for facility in facilities:
                facility_name = facility.get("name", "未知設施")
                openings = facility.get("openings", [])

                logger.info("處理設施: %s, 開度數: %d", facility_name, len(openings))

                if not openings:
                    continue

                # 收集所有數據點
                all_data = []

                for opening in openings:
                    opening_value = opening.get("opening", "未知")
                    data_points = opening.get("data", [])

                    for point in data_points:
                        all_data.append(
                            {
                                "開度": opening_value,
                                "水位(m)": point.get("water_level", 0),
                                "流量(cms)": point.get("flow", 0),
                            }
                        )

                if all_data:
                    # 創建 DataFrame
                    df = pd.DataFrame(all_data)

                    # 清理工作表名稱（Excel 工作表名稱限制）
                    sheet_name = facility_name[:31]  # Excel 工作表名稱最多31字符
                    sheet_name = (
                        sheet_name.replace("/", "_")
                        .replace("\\", "_")
                        .replace("*", "_")
                    )
                    sheet_name = (
                        sheet_name.replace("?", "_").replace("[", "_").replace("]", "_")
                    )

                    # 寫入數據
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    logger.info("寫入設施 '%s' 數據: %d 筆記錄", facility_name, len(df))

            # 🔧 統一：創建設施統計工作表
            try:
                summary_data = []

                for facility in facilities:
                    facility_name = facility.get("name", "未知設施")
                    openings = facility.get("openings", [])

                    total_points = sum(
                        len(opening.get("data", [])) for opening in openings
                    )
                    opening_list = [
                        str(opening.get("opening", "未知")) for opening in openings
                    ]

                    summary_data.append(
                        {
                            "設施名稱": facility_name,
                            "開度數量": len(openings),
                            "開度清單": ", ".join(opening_list),
                            "數據點總數": total_points,
                        }
                    )

                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name="設施統計", index=False)
                    logger.info("寫入設施統計: %d 個設施", len(summary_data))

            except Exception as summary_error:
                logger.warning("添加設施統計失敗: %s", str(summary_error))

            # 🔧 統一：添加統計資訊工作表
            try:
                basic_info = {
                    "項目": [
                        "數據類型",
                        "設施總數",
                        "總開度數",
                        "總數據點數",
                        "下載時間",
                    ],
                    "數值": [
                        "排洪設施數據",
                        len(facilities),
                        sum(len(f.get("openings", [])) for f in facilities),
                        sum(
                            len(op.get("data", []))
                            for f in facilities
                            for op in f.get("openings", [])
                        ),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ],
                }

                basic_info_df = pd.DataFrame(basic_info)
                basic_info_df.to_excel(writer, sheet_name="統計資訊", index=False)
                logger.info("添加統計資訊工作表")

            except Exception as info_error:
                logger.warning("添加統計資訊失敗: %s", str(info_error))

        output.seek(0)
        excel_content = output.read()

        logger.info("Excel 檔案大小: %d bytes", len(excel_content))

        if len(excel_content) == 0:
            logger.error("生成的 Excel 檔案為空")
            return JsonResponse({"success": False, "message": "生成的檔案為空"})

        # 🔧 統一：生成檔案名稱格式
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "步驟3_排洪設施數據_%s.xlsx" % timestamp

        # 設定 HTTP 響應
        response = HttpResponse(
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response["Content-Length"] = len(excel_content)

        logger.info(
            "步驟3數據下載成功: %s, 大小: %d bytes", filename, len(excel_content)
        )
        return response

    except (ValueError, TypeError, KeyError, IOError) as e:
        logger.error("步驟3下載失敗: %s", str(e), exc_info=True)
        return JsonResponse({"success": False, "message": "步驟3下載失敗: %s" % str(e)})


def handle_step4_download(step4_data):
    """處理步驟4的條件設定下載"""
    try:
        output = io.BytesIO()
        df = pd.DataFrame(step4_data)
        # 欄位名稱轉中文
        col_map = {
            "facility": "設施",
            "opening": "開度",
            "time_control": "時間控制(hr)",
            "flow_control_before": "流量控制(洪峰前)(cms)",
            "flow_control_after": "流量控制(洪峰後)(cms)",
            "waterlevel_control_before": "水位控制(洪峰前)(m)",
            "waterlevel_control_after": "水位控制(洪峰後)(m)"
        }
        df = df.rename(columns=col_map)
        # 將陣列欄位轉字串
        for col in ["時間控制(hr)", "流量控制(洪峰前)(cms)", "流量控制(洪峰後)(cms)", "水位控制(洪峰前)(m)", "水位控制(洪峰後)(m)"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, (list, tuple)) else x)
        # 寫入 Excel
        df = df.sort_values(by=["設施", "開度"])
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="排洪規則設定", index=False)
        output.seek(0)
        excel_content = output.read()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"步驟4_排洪規則設定_{timestamp}.xlsx"
        response = HttpResponse(
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(excel_content)
        return response
    except Exception as e:
        return JsonResponse({"success": False, "message": f"步驟4下載失敗: {e}"})
