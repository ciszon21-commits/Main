"""
CODIS 氣象資料爬蟲模組
使用 Selenium 自動化瀏覽器操作，從中央氣象署觀測資料查詢系統爬取月報表資料
"""
import time
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class CODISScraper:
    """中央氣象署 CODIS 資料爬蟲類別"""
    
    BASE_URL = "https://codis.cwa.gov.tw/StationData"
    
    # 預設測站資訊
    DEFAULT_STATIONS = {
        '恆春': {
            'code': '467590',
            'city': '屏東縣',
            'address': '恆春鎮天文路50號',
            'region': '南區',
            'latitude': 22.0039,
            'longitude': 120.7463,
            'altitude': 22.3,
            'established_date': '1896-01-01'
        }
    }
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        初始化爬蟲
        
        Args:
            headless: 是否使用 headless 模式
            timeout: 等待超時時間（秒）
        """
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None
        
    def _setup_driver(self) -> webdriver.Chrome:
        """設定並初始化 Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=zh-TW")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        return driver
    
    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """將字串解析為 Decimal，處理空值和無效值"""
        if not value or value.strip() in ['', '-', '...', 'T', 'X', '/']:
            return None
        try:
            cleaned = value.strip().replace(',', '')
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字串"""
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(date_str.strip(), "%Y/%m/%d").date()
            except ValueError:
                return None
    
    def start(self):
        """啟動瀏覽器"""
        if not self.driver:
            self.driver = self._setup_driver()
            logger.info("WebDriver 已啟動")
    
    def stop(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver 已關閉")
    
    def navigate_to_station(self, station_name: str) -> bool:
        """
        導航到指定測站頁面
        
        Args:
            station_name: 測站名稱（如：恆春）
            
        Returns:
            bool: 是否成功導航
        """
        try:
            self.driver.get(self.BASE_URL)
            wait = WebDriverWait(self.driver, self.timeout)
            
            # 等待頁面載入
            time.sleep(1.5)
            
            # 找到站名站號輸入框並輸入 (使用 list 屬性定位)
            station_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[list="station_name"]'))
            )
            station_input.clear()
            station_input.send_keys(station_name)
            time.sleep(0.5)
            # 按 Enter 確認選擇
            station_input.send_keys(Keys.ENTER)
            time.sleep(1)
            
            # 點擊地圖上的測站標記
            station_marker = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".leaflet-marker-icon"))
            )
            station_marker.click()
            time.sleep(1)
            
            logger.info(f"已導航到測站: {station_name}")
            return True
            
        except TimeoutException:
            logger.error(f"導航到測站 {station_name} 超時")
            return False
        except Exception as e:
            logger.error(f"導航到測站 {station_name} 失敗: {e}")
            return False
    
    def open_monthly_report(self) -> bool:
        """
        打開月報表頁面
        
        Returns:
            bool: 是否成功打開
        """
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            
            # 點擊「資料圖表展示」按鈕
            chart_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '資料圖表展示')]"))
            )
            chart_btn.click()
            time.sleep(1.5)
            
            # 點擊左側選單的「月報表(逐日資料)」
            monthly_report_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '月報表(逐日資料)')]"))
            )
            monthly_report_btn.click()
            time.sleep(1.5)
            
            logger.info("已打開月報表頁面")
            return True
            
        except TimeoutException:
            logger.error("打開月報表頁面超時")
            return False
        except Exception as e:
            logger.error(f"打開月報表頁面失敗: {e}")
            return False
    
    def navigate_to_date(self, target_year: int, target_month: int) -> bool:
        """
        使用 < 和 > 按鈕導航到指定的年月
        CODIS 使用 <div class="datetime-tool-prev-next"> 而非 <button>
        
        Args:
            target_year: 目標年份
            target_month: 目標月份
            
        Returns:
            bool: 是否成功導航
        """
        try:
            time.sleep(1)
            
            # 讀取當前顯示的年月 - 使用 CODIS 特定的選擇器
            current_date_js = """
            // 找到月報表的日期輸入框 (觀測時間旁)
            var input = document.querySelector('input.vdatetime-input.datetime-selector[placeholder="請選擇月份"]');
            if (input && input.value) {
                return input.value;
            }
            // 備用：找任何 vdatetime-input
            var inputs = document.querySelectorAll('input.vdatetime-input');
            for (var inp of inputs) {
                if (inp.value && inp.value.match(/\\d{4}\\/\\d{1,2}/)) {
                    return inp.value;
                }
            }
            return null;
            """
            
            current_date = self.driver.execute_script(current_date_js)
            logger.info(f"當前日期顯示: {current_date}")
            
            if current_date:
                # 格式可能是 2026/01 或 2026-01
                parts = current_date.replace('-', '/').split('/')
                current_year = int(parts[0])
                current_month = int(parts[1])
            else:
                # 如果無法取得當前日期，假設是當前月份
                current_year = datetime.now().year
                current_month = datetime.now().month
                logger.warning(f"無法取得當前日期，假設為 {current_year}/{current_month}")
            
            # 計算需要移動多少個月
            months_diff = (target_year - current_year) * 12 + (target_month - current_month)
            
            logger.info(f"目標: {target_year}/{target_month}, 當前: {current_year}/{current_month}, 差距: {months_diff} 個月")
            
            if months_diff == 0:
                logger.info("已在目標日期，不需要導航")
                return True
            
            # 決定點擊哪個按鈕
            if months_diff > 0:
                direction = ">"
            else:
                direction = "<"
                months_diff = abs(months_diff)
            
            # 使用 JavaScript 找到並點擊 < 或 > 按鈕 (CODIS 使用 div.datetime-tool-prev-next)
            for i in range(months_diff):
                click_js = f"""
                // 找到「觀測時間」標籤內的導航按鈕
                var labels = document.querySelectorAll('label');
                var timeLabel = null;
                for (var lbl of labels) {{
                    if (lbl.textContent.includes('觀測時間') && lbl.offsetParent !== null) {{
                        timeLabel = lbl;
                        break;
                    }}
                }}
                
                if (timeLabel) {{
                    // 在該 label 內找 datetime-tool-prev-next
                    var navBtns = timeLabel.querySelectorAll('.datetime-tool-prev-next');
                    for (var btn of navBtns) {{
                        if (btn.textContent.trim() === '{direction}') {{
                            btn.click();
                            return true;
                        }}
                    }}
                }}
                
                // 備用：直接在整個頁面找
                var allNavBtns = document.querySelectorAll('.datetime-tool-prev-next');
                for (var btn of allNavBtns) {{
                    if (btn.textContent.trim() === '{direction}' && btn.offsetParent !== null) {{
                        btn.click();
                        return true;
                    }}
                }}
                
                return false;
                """
                
                result = self.driver.execute_script(click_js)
                if not result:
                    logger.error(f"找不到 {direction} 按鈕")
                    return False
                
                logger.info(f"點擊 {direction} 按鈕 ({i+1}/{months_diff})")
                
                # 等待表格重新載入 - 這是關鍵！
                time.sleep(0.8)
                
                # 等待載入指示器消失
                wait_for_load_js = """
                return new Promise(resolve => {
                    var checkInterval = setInterval(() => {
                        var overlay = document.querySelector('.v-table-loading-overlay, .loading-overlay, .spinner');
                        if (!overlay || overlay.style.display === 'none' || overlay.offsetParent === null) {
                            clearInterval(checkInterval);
                            resolve(true);
                        }
                    }, 200);
                    // 最多等待 5 秒
                    setTimeout(() => {
                        clearInterval(checkInterval);
                        resolve(true);
                    }, 5000);
                });
                """
                try:
                    self.driver.execute_script(wait_for_load_js)
                except:
                    time.sleep(1)
            
            # 最後等待資料載入完成
            time.sleep(1.5)
            
            # 驗證日期是否正確
            new_date = self.driver.execute_script(current_date_js)
            logger.info(f"導航後日期顯示: {new_date}")
            
            logger.info(f"已導航到 {target_year}/{target_month}")
            return True
            
        except Exception as e:
            logger.error(f"導航到日期失敗: {e}")
            return False

    
    def scrape_monthly_data(self, year: int = None, month: int = None) -> List[Dict[str, Any]]:
        """
        爬取月報表資料
        
        Args:
            year: 年份（預設為當前年份）
            month: 月份（預設為當前月份）
            
        Returns:
            List[Dict]: 每日氣象資料列表
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
            
        data_list = []
        
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            time.sleep(1)
            
            # 等待月報表表格載入 - 使用表格 ID #report_month
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#report_month"))
            )
            time.sleep(1)
            
            # 使用 JavaScript 抓取 #report_month 表格的資料
            js_script = """
            var result = {headers: [], rows: []};
            
            // 找到 report_month 表格
            var table = document.querySelector('#report_month');
            if (!table) return result;
            
            // 取得最後一行表頭（縮寫行）- 表頭可能在 span 內
            var headerRows = table.querySelectorAll('thead tr');
            if (headerRows.length > 0) {
                var lastRow = headerRows[headerRows.length - 1];
                var ths = lastRow.querySelectorAll('th');
                ths.forEach(function(th) {
                    // 嘗試從 span 取得文字，否則從 th 直接取得
                    var span = th.querySelector('span');
                    var text = span ? span.innerText.trim() : th.innerText.trim();
                    text = text.replace(/\\n/g, ' ');
                    result.headers.push(text);
                });
            }
            
            // 取得資料行
            var tbody = table.querySelector('tbody');
            if (tbody) {
                var trs = tbody.querySelectorAll('tr');
                trs.forEach(function(tr) {
                    var rowData = [];
                    var tds = tr.querySelectorAll('td');
                    tds.forEach(function(td) {
                        rowData.push(td.innerText.trim());
                    });
                    if (rowData.length > 0) {
                        result.rows.push(rowData);
                    }
                });
            }
            
            return result;
            """
            
            table_data = self.driver.execute_script(js_script)
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            logger.info(f"表頭欄位數量: {len(headers)}")
            logger.info(f"表頭欄位: {headers}")
            logger.info(f"資料行數: {len(rows)}")
            
            # 找出 WS 和 WD 欄位的索引
            ws_index = next((i for i, h in enumerate(headers) if h == 'WS'), -1)
            wd_index = next((i for i, h in enumerate(headers) if h == 'WD'), -1)
            logger.info(f"WS索引: {ws_index}, WD索引: {wd_index}")
            
            for row in rows:
                row_data = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_data[headers[i]] = value
                    else:
                        row_data[f'column_{i}'] = value
                
                # 解析日期
                day_str = row_data.get('ObsTime', row_data.get('觀測時間', ''))
                if day_str:
                    try:
                        day = int(day_str)
                        obs_date = date(year, month, day)
                        row_data['obs_date'] = obs_date.isoformat()
                    except (ValueError, TypeError):
                        pass
                
                # 儲存原始資料
                row_data['raw_data'] = dict(row_data)
                data_list.append(row_data)
                
                # Debug: 輸出第一筆資料的 WS/WD
                if len(data_list) == 1:
                    logger.info(f"第一筆 WS: {row_data.get('WS', 'N/A')}, WD: {row_data.get('WD', 'N/A')}")
            
            logger.info(f"已爬取 {len(data_list)} 筆月報表資料 ({year}/{month})")
            return data_list
            
        except TimeoutException:
            logger.error("爬取月報表資料超時 - 可能找不到 WS 欄位")
            return []
        except Exception as e:
            logger.error(f"爬取月報表資料失敗: {e}")
            return []
    
    def scrape_station_monthly_report(
        self, 
        station_name: str = '恆春',
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """
        完整的測站月報表爬取流程
        
        Args:
            station_name: 測站名稱
            year: 年份
            month: 月份
            
        Returns:
            Dict: 包含測站資訊和月報表資料
        """
        result = {
            'success': False,
            'station': None,
            'data': [],
            'error': None,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            self.start()
            
            # 取得測站資訊
            station_info = self.DEFAULT_STATIONS.get(station_name, {})
            result['station'] = {
                'name': station_name,
                **station_info
            }
            
            # 導航到測站
            if not self.navigate_to_station(station_name):
                result['error'] = f"無法導航到測站: {station_name}"
                return result
            
            # 打開月報表
            if not self.open_monthly_report():
                result['error'] = "無法打開月報表頁面"
                return result
            
            # 設定目標年月
            target_year = year if year else datetime.now().year
            target_month = month if month else datetime.now().month
            
            # 導航到指定的年月
            if not self.navigate_to_date(target_year, target_month):
                logger.warning(f"導航到 {target_year}/{target_month} 失敗，使用預設日期")
            
            # 爬取資料
            data = self.scrape_monthly_data(target_year, target_month)
            result['data'] = data
            result['success'] = len(data) > 0
            
            if not data:
                result['error'] = "未能爬取到任何資料"
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"爬取過程發生錯誤: {e}")
            return result
            
        finally:
            self.stop()
    
    def scrape_station_date_range(
        self, 
        station_name: str = '恆春',
        start_year: int = None,
        start_month: int = None,
        end_year: int = None,
        end_month: int = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        擷取測站指定日期範圍的月報表資料
        從結束年月開始，往前爬取到起始年月（從最新開始）
        
        Args:
            station_name: 測站名稱
            start_year: 起始年份
            start_month: 起始月份
            end_year: 結束年份
            end_month: 結束月份
            progress_callback: 進度回調函數，接收 (current_year, current_month, index, total) 參數
            
        Returns:
            Dict: 包含測站資訊和所有月份的資料
        """
        result = {
            'success': False,
            'station': None,
            'data': [],
            'months_collected': [],
            'current_progress': None,
            'error': None,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # 設定預設值
            now = datetime.now()
            if start_year is None:
                start_year = now.year
            if start_month is None:
                start_month = now.month
            if end_year is None:
                end_year = now.year
            if end_month is None:
                end_month = now.month
            
            # 驗證日期範圍
            start_date = date(start_year, start_month, 1)
            end_date = date(end_year, end_month, 1)
            
            if start_date > end_date:
                result['error'] = f"起始日期 ({start_year}/{start_month}) 不能晚於結束日期 ({end_year}/{end_month})"
                return result
            
            self.start()
            
            # 取得測站資訊
            station_info = self.DEFAULT_STATIONS.get(station_name, {})
            result['station'] = {
                'name': station_name,
                **station_info
            }
            
            # 導航到測站
            if not self.navigate_to_station(station_name):
                result['error'] = f"無法導航到測站: {station_name}"
                return result
            
            # 打開月報表
            if not self.open_monthly_report():
                result['error'] = "無法打開月報表頁面"
                return result
            
            # 從結束年月開始（最接近現在的日期）
            if not self.navigate_to_date(end_year, end_month):
                logger.warning(f"導航到結束日期 {end_year}/{end_month} 失敗")
            
            # 計算需要爬取的月份數量
            months_count = (end_year - start_year) * 12 + (end_month - start_month) + 1
            logger.info(f"將爬取 {months_count} 個月的資料: {end_year}/{end_month} 到 {start_year}/{start_month} (從最新開始)")
            
            all_data = []
            current_year = end_year
            current_month = end_month
            
            for i in range(months_count):
                # 更新進度
                result['current_progress'] = {
                    'year': current_year,
                    'month': current_month,
                    'index': i + 1,
                    'total': months_count
                }
                
                logger.info(f"正在爬取 {current_year}/{current_month} ({i+1}/{months_count})")
                
                # 呼叫進度回調
                if progress_callback:
                    progress_callback(current_year, current_month, i + 1, months_count)
                
                # 爬取當前月份的資料
                monthly_data = self.scrape_monthly_data(current_year, current_month)
                
                if monthly_data:
                    all_data.extend(monthly_data)
                    result['months_collected'].append(f"{current_year}/{current_month:02d}")
                    logger.info(f"成功爬取 {current_year}/{current_month}: {len(monthly_data)} 筆資料")
                else:
                    logger.warning(f"未能爬取 {current_year}/{current_month} 的資料")
                
                # 如果不是最後一個月，點擊 < 移動到上一個月
                if i < months_count - 1:
                    # 使用 < 按鈕移動到上一個月
                    prev_js = """
                    var labels = document.querySelectorAll('label');
                    for (var lbl of labels) {
                        if (lbl.textContent.includes('觀測時間') && lbl.offsetParent !== null) {
                            var navBtns = lbl.querySelectorAll('.datetime-tool-prev-next');
                            for (var btn of navBtns) {
                                if (btn.textContent.trim() === '<') {
                                    btn.click();
                                    return true;
                                }
                            }
                        }
                    }
                    // 備用
                    var allBtns = document.querySelectorAll('.datetime-tool-prev-next');
                    for (var btn of allBtns) {
                        if (btn.textContent.trim() === '<' && btn.offsetParent !== null) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                    """
                    
                    clicked = self.driver.execute_script(prev_js)
                    if clicked:
                        # 等待資料載入
                        time.sleep(1.5)
                        logger.info(f"已點擊 < 按鈕，移動到上一個月")
                    else:
                        logger.error("無法點擊 < 按鈕移動到上一個月")
                        break
                    
                    # 更新當前年月 (往前)
                    current_month -= 1
                    if current_month < 1:
                        current_month = 12
                        current_year -= 1
            
            # 資料排序（按日期從舊到新）
            all_data.sort(key=lambda x: x.get('obs_date', ''))
            
            # 月份排序（從舊到新）
            result['months_collected'].sort()
            
            result['data'] = all_data
            result['success'] = len(all_data) > 0
            result['current_progress'] = {
                'year': None,
                'month': None,
                'index': months_count,
                'total': months_count,
                'completed': True
            }
            
            if not all_data:
                result['error'] = "未能爬取到任何資料"
            else:
                logger.info(f"總共爬取 {len(all_data)} 筆資料，涵蓋 {len(result['months_collected'])} 個月")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"爬取日期範圍資料時發生錯誤: {e}")
            return result
            
        finally:
            self.stop()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
