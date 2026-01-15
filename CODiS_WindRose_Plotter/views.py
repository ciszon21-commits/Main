import json
import logging
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .scraper import CODISScraper

logger = logging.getLogger(__name__)


def process_wind_rose_data(data):
    """
    處理風速風向資料，轉換成風玫瑰圖所需格式
    
    風向分為 16 方位：N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW
    風速分為 4 組：0-3, 3-6, 6-9, >9 m/s
    
    Args:
        data: 包含 wind_speed 和 wind_direction 的資料列表
        
    Returns:
        dict: 風玫瑰圖資料
    """
    # 16 方位定義 (每個方位佔 22.5 度)
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    # 風速分組
    speed_bins = [
        {'name': '0-3 m/s', 'min': 0, 'max': 3, 'color': '#2ecc71'},   # 綠
        {'name': '3-6 m/s', 'min': 3, 'max': 6, 'color': '#f1c40f'},   # 黃
        {'name': '6-9 m/s', 'min': 6, 'max': 9, 'color': '#e67e22'},   # 橘
        {'name': '>9 m/s', 'min': 9, 'max': float('inf'), 'color': '#e74c3c'}  # 紅
    ]
    
    # 初始化計數矩陣：16 方位 × 4 風速組
    wind_rose = {bin_info['name']: [0] * 16 for bin_info in speed_bins}
    total_count = 0
    valid_count = 0
    
    for row in data:
        try:
            # 解析風速
            ws = row.get('wind_speed', '-')
            wd = row.get('wind_direction', '-')
            
            if ws == '-' or wd == '-' or ws is None or wd is None:
                continue
            
            wind_speed = float(str(ws).replace(' ', ''))
            wind_direction = float(str(wd).replace(' ', ''))
            
            total_count += 1
            
            # 處理風向：轉換為 0-360 度
            wind_direction = wind_direction % 360
            
            # 計算方位索引 (每個方位 22.5 度，從北開始，偏移 11.25 度使北在中間)
            dir_index = int((wind_direction + 11.25) / 22.5) % 16
            
            # 判斷風速分組
            for i, bin_info in enumerate(speed_bins):
                if bin_info['min'] <= wind_speed < bin_info['max']:
                    wind_rose[bin_info['name']][dir_index] += 1
                    valid_count += 1
                    break
                    
        except (ValueError, TypeError) as e:
            continue
    
    # 轉換為百分比 (相對於有效資料總數)
    if valid_count > 0:
        for bin_name in wind_rose:
            wind_rose[bin_name] = [round(count / valid_count * 100, 2) for count in wind_rose[bin_name]]
    
    return {
        'directions': directions,
        'speed_bins': [{'name': b['name'], 'color': b['color']} for b in speed_bins],
        'data': wind_rose,
        'total_count': total_count,
        'valid_count': valid_count
    }


def index(request):
    """
    主頁面 - 顯示氣象資料搜尋介面
    """
    selected_year = request.GET.get('year', datetime.now().year)
    selected_month = request.GET.get('month', datetime.now().month)
    station_name = request.GET.get('station_name', '')
    
    try:
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = datetime.now().year
        selected_month = datetime.now().month
    
    # 產生年份選項 (1980 到現在)
    current_year = datetime.now().year
    years = list(range(current_year, 1979, -1))
    
    # 月份選項
    months = list(range(1, 13))
    
    context = {
        'years': years,
        'months': months,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'station_name': station_name,
        'reports': [],  # 初始無資料
    }
    
    return render(request, 'CODiS_WindRose_Plotter/index.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def search_data(request):
    """
    搜尋資料 - 使用 Server-Sent Events 串流即時進度
    支援單月或日期範圍搜尋
    """
    from django.http import StreamingHttpResponse
    import time as time_module
    from datetime import date
    from queue import Queue
    import threading
    
    try:
        body = json.loads(request.body) if request.body else {}
        station_name = body.get('station_name', '臺北')
        headless = body.get('headless', False)
        
        # 日期範圍參數
        start_year = body.get('start_year')
        start_month = body.get('start_month')
        end_year = body.get('end_year')
        end_month = body.get('end_month')
        
        # 單月參數 (向後相容)
        year = body.get('year')
        month = body.get('month')
        
        if not station_name:
            return JsonResponse({
                'success': False,
                'error': '請輸入測站名稱'
            }, status=400)
        
        # 如果是日期範圍搜尋，使用 SSE 串流
        if start_year and start_month and end_year and end_month:
            start_year = int(start_year)
            start_month = int(start_month)
            end_year = int(end_year)
            end_month = int(end_month)
            
            progress_queue = Queue()
            result_holder = {'result': None}
            
            def progress_callback(current_year, current_month, index, total):
                progress_queue.put({
                    'type': 'progress',
                    'year': current_year,
                    'month': current_month,
                    'index': index,
                    'total': total
                })
            
            def run_scraper():
                scraper = CODISScraper(headless=headless)
                result = scraper.scrape_station_date_range(
                    station_name=station_name,
                    start_year=start_year,
                    start_month=start_month,
                    end_year=end_year,
                    end_month=end_month,
                    progress_callback=progress_callback
                )
                result_holder['result'] = result
                progress_queue.put({'type': 'done'})
            
            # 啟動爬蟲線程
            scraper_thread = threading.Thread(target=run_scraper)
            scraper_thread.start()
            
            def event_stream():
                while True:
                    try:
                        msg = progress_queue.get(timeout=120)
                        if msg['type'] == 'progress':
                            yield f"data: {json.dumps(msg)}\n\n"
                        elif msg['type'] == 'done':
                            scraper_thread.join()
                            result = result_holder['result']
                            
                            if result and result['success']:
                                # 處理原始資料
                                reports = []
                                for row in result['data']:
                                    obs_date = row.get('obs_date', '')
                                    wind_speed = row.get('WS', row.get('風速', row.get('WSmean', '-')))
                                    wind_direction = row.get('WD', row.get('風向', row.get('WDmean', '-')))
                                    reports.append({
                                        'obs_date': obs_date,
                                        'wind_speed': wind_speed if wind_speed else '-',
                                        'wind_direction': wind_direction if wind_direction else '-',
                                    })
                                
                                # 處理風玫瑰圖資料
                                wind_rose_data = process_wind_rose_data(reports)
                                
                                # 處理季度資料 (Q1-Q4)
                                def get_quarter_reports(all_reports, months):
                                    return [
                                        r for r in all_reports 
                                        if r['obs_date'] and int(r['obs_date'].split('-')[1]) in months
                                    ]

                                q1_reports = get_quarter_reports(reports, [1, 2, 3])
                                q2_reports = get_quarter_reports(reports, [4, 5, 6])
                                q3_reports = get_quarter_reports(reports, [7, 8, 9])
                                q4_reports = get_quarter_reports(reports, [10, 11, 12])

                                final_msg = {
                                    'type': 'complete',
                                    'success': True,
                                    'message': f'已成功搜尋 {len(reports)} 筆資料，涵蓋 {len(result.get("months_collected", []))} 個月',
                                    'station': station_name,
                                    'start_year': start_year,
                                    'start_month': start_month,
                                    'end_year': end_year,
                                    'end_month': end_month,
                                    'months_collected': result.get('months_collected', []),
                                    'wind_rose_data': wind_rose_data,
                                    'q1_data': process_wind_rose_data(q1_reports),
                                    'q2_data': process_wind_rose_data(q2_reports),
                                    'q3_data': process_wind_rose_data(q3_reports),
                                    'q4_data': process_wind_rose_data(q4_reports)
                                }
                            else:
                                final_msg = {
                                    'type': 'complete',
                                    'success': False,
                                    'error': result.get('error', '搜尋失敗') if result else '搜尋失敗'
                                }
                            yield f"data: {json.dumps(final_msg)}\n\n"
                            break
                    except:
                        break
            
            response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
        else:
            # 單月搜尋 (向後相容) - 使用普通 JSON 回應
            if year:
                year = int(year)
            if month:
                month = int(month)
            
            scraper = CODISScraper(headless=headless)
            result = scraper.scrape_station_monthly_report(
                station_name=station_name,
                year=year,
                month=month
            )
            
            if result['success']:
                reports = []
                for row in result['data']:
                    obs_date = row.get('obs_date', '')
                    wind_speed = row.get('WS', row.get('風速', row.get('WSmean', '-')))
                    wind_direction = row.get('WD', row.get('風向', row.get('WDmean', '-')))
                    
                    reports.append({
                        'obs_date': obs_date,
                        'wind_speed': wind_speed if wind_speed else '-',
                        'wind_direction': wind_direction if wind_direction else '-',
                    })
                
                return JsonResponse({
                    'success': True,
                    'message': f'已成功搜尋 {len(reports)} 筆資料',
                    'station': station_name,
                    'year': year,
                    'month': month,
                    'data': reports
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', '搜尋失敗')
                }, status=400)
            
    except Exception as e:
        logger.error(f"搜尋資料時發生錯誤: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


