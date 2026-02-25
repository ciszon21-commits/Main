"""
DTM (數值地形模型) 資料同步指令
=================================
從 OpenSearch 搜尋 .xyz 檔案，解析座標並在 GeoDataHub 建立對應的地點標記。

用法:
    python manage.py sync_dtm [--limit N] [--batch-size N] [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging
import time
import os
import re

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '從 OpenSearch 同步 DTM (.xyz) 檔案至 GeoDataHub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='限制處理筆數 (0 表示不限)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='批次寫入量 (預設 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='預覽模式，不實際寫入資料'
        )
        parser.add_argument(
            '--read-files',
            action='store_true',
            help='讀取實際 XYZ 檔案以取得精確座標 (會從 UNC 路徑讀取檔案)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.3,
            help='讀取檔案間的延遲秒數 (預設 0.3 秒，避免網路過載)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        read_files = options['read_files']
        delay = options['delay']

        self.stdout.write(self.style.SUCCESS(
            f'開始同步 DTM 資料... (limit={limit}, batch_size={batch_size}, dry_run={dry_run})'
        ))

        service = DTMSyncService()
        start_time = time.time()

        try:
            results = service.sync_dtm_data(
                limit=limit,
                batch_size=batch_size,
                dry_run=dry_run,
                read_files=read_files,
                delay=delay
            )

            elapsed = time.time() - start_time

            self.stdout.write(self.style.SUCCESS('DTM 同步任務執行完畢！'))
            self.stdout.write(f'執行耗時: {elapsed:.2f} 秒')
            self.stdout.write(f'搜尋到: {results.get("found", 0)} 筆')
            self.stdout.write(f'新增: {results.get("created", 0)} 筆')
            self.stdout.write(f'跳過: {results.get("skipped", 0)} 筆')
            self.stdout.write(f'無法定位: {results.get("no_location", 0)} 筆')
            if read_files:
                self.stdout.write(f'檔案讀取: {results.get("files_read", 0)} 筆')

            if dry_run:
                self.stdout.write(self.style.WARNING('(預覽模式，未實際寫入資料)'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'發生錯誤: {str(e)}'))
            logger.exception('DTM sync failed')


class DTMSyncService:
    """DTM 資料同步服務"""

    # TWD97 座標系統參數 (EPSG:3826)
    # 用於判斷和轉換座標
    TWD97_X_MIN = 140000   # 約臺灣西界
    TWD97_X_MAX = 360000   # 約臺灣東界
    TWD97_Y_MIN = 2400000  # 約臺灣南界
    TWD97_Y_MAX = 2850000  # 約臺灣北界

    def __init__(self):
        from GeoDataHub.models import GeoDataSource, GeoCategory, GeoLocation, GeoSyncLog
        from GeoDataHub.services import MapGridService
        self.GeoDataSource = GeoDataSource
        self.GeoCategory = GeoCategory
        self.GeoLocation = GeoLocation
        self.GeoSyncLog = GeoSyncLog
        self.MapGridService = MapGridService

        # 取得 OpenSearch client
        try:
            from OpenSearch.services import get_client, search
            self.get_client = get_client
            self.search = search
        except ImportError:
            raise ImportError('無法載入 OpenSearch 服務')

    def sync_dtm_data(self, limit: int = 0, batch_size: int = 100, dry_run: bool = False,
                       read_files: bool = False, delay: float = 0.3) -> dict:
        """
        從 OpenSearch 同步 DTM 資料

        Args:
            limit: 限制處理筆數 (0 = 不限)
            batch_size: 批次寫入量
            dry_run: 預覽模式
            read_files: 是否讀取實際 XYZ 檔案
            delay: 讀取檔案間的延遲秒數

        Returns:
            執行結果統計
        """
        results = {
            'found': 0,
            'created': 0,
            'skipped': 0,
            'no_location': 0,
            'files_read': 0,
            'details': []
        }

        # 建立或取得 DTM 分類
        category, _ = self.GeoCategory.objects.get_or_create(
            name='DTM',
            defaults={
                'icon': '🏔️',
                'color': '#8B4513',  # 棕色
                'description': '數值地形模型 (Digital Terrain Model) - XYZ 點雲資料'
            }
        )

        # 預載已存在的文件 ID
        existing_doc_ids = set(
            self.GeoDataSource.objects.filter(
                category=category
            ).values_list('opensearch_doc_id', flat=True)
        )

        # 從 OpenSearch 搜尋 .xyz 檔案
        all_hits = self._search_xyz_files(limit=limit)
        results['found'] = len(all_hits)

        # 批次處理
        new_items = []
        for hit in all_hits:
            doc_id = hit.get('_id', '')
            source = hit.get('_source', {})
            index_name = hit.get('_index', '')

            # 檢查是否已存在
            if doc_id in existing_doc_ids:
                results['skipped'] += 1
                continue

            try:
                # 取得檔案路徑
                full_path = source.get('path', {}).get('real', '') if isinstance(source.get('path'), dict) else ''
                
                # 解析座標
                location = None
                
                # 如果啟用檔案讀取，嘗試從實際檔案讀取座標
                if read_files and full_path:
                    location = self._read_xyz_file_coords(full_path)
                    if location:
                        results['files_read'] += 1
                    # 加入延遲避免網路過載
                    time.sleep(delay)
                
                # 如果沒有從檔案取得座標，使用原有的解析方法
                if not location:
                    location = self._extract_location(source)

                if not location:
                    results['no_location'] += 1
                    if not dry_run:
                        results['details'].append({
                            'doc_id': doc_id,
                            'filename': source.get('file', {}).get('filename', ''),
                            'reason': '無法解析座標'
                        })
                    continue

                # 取得標題
                title = (
                    source.get('title') or
                    source.get('file', {}).get('filename') or
                    source.get('filename') or
                    os.path.basename(source.get('path', {}).get('real', '')) or
                    f'DTM_{doc_id[:8]}'
                )

                if dry_run:
                    source_type = '檔案' if results['files_read'] > 0 else '路徑'
                    print(f'  [預覽] {title}')
                    print(f'         座標: ({location["lat"]:.6f}, {location["lng"]:.6f}) [{source_type}]')
                    results['created'] += 1
                    continue

                # 建立 GeoLocation
                geo_location = self.GeoLocation.objects.create(
                    latitude=Decimal(str(location['lat'])),
                    longitude=Decimal(str(location['lng'])),
                    geometry_type=self.GeoLocation.GeometryType.POINT,
                    address=source.get('path', {}).get('real', ''),
                )

                # 建立 GeoDataSource
                ds = self.GeoDataSource(
                    title=title,
                    description=source.get('content', '')[:500] if source.get('content') else '',
                    source_type=self.GeoDataSource.SourceType.OPENSEARCH,
                    category=category,
                    location=geo_location,
                    opensearch_index=index_name,
                    opensearch_doc_id=doc_id,
                    metadata=source,
                    is_visible=True
                )
                new_items.append(ds)

                # 批次寫入
                if len(new_items) >= batch_size:
                    with transaction.atomic():
                        self.GeoDataSource.objects.bulk_create(new_items)
                    results['created'] += len(new_items)
                    new_items = []

            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'doc_id': doc_id,
                    'error': str(e)
                })
                logger.warning(f'處理 DTM 文件 {doc_id} 失敗: {e}')

        # 寫入剩餘項目
        if new_items and not dry_run:
            with transaction.atomic():
                self.GeoDataSource.objects.bulk_create(new_items)
            results['created'] += len(new_items)

        return results

    def _search_xyz_files(self, limit: int = 0) -> list:
        """
        從 OpenSearch 搜尋所有 .xyz 檔案

        Args:
            limit: 限制數量

        Returns:
            搜尋結果列表
        """
        all_hits = []
        size = min(limit, 100) if limit else 100
        from_ = 0

        while True:
            response = self.search(
                query='ext:xyz',
                indices='*',
                size=size,
                from_=from_
            )

            hits = response.get('hits', {}).get('hits', [])
            if not hits:
                break

            all_hits.extend(hits)

            if limit and len(all_hits) >= limit:
                all_hits = all_hits[:limit]
                break

            from_ += len(hits)

            # 防止無限迴圈
            if from_ >= response.get('hits', {}).get('total', {}).get('value', 0):
                break

        return all_hits

    def _read_xyz_file_coords(self, unc_path: str) -> dict:
        """
        從 UNC 路徑讀取 XYZ 檔案，取得第一筆和最後一筆座標並計算中心點
        
        只讀取檔案的前 20 行和最後 20 行以減少 I/O
        
        Args:
            unc_path: 檔案的 UNC 路徑 (例如 //200.200.5.70/path/file.xyz)
        
        Returns:
            {'lat': float, 'lng': float} 或 None
        """
        try:
            # 將 UNC 路徑轉換為 Windows 格式
            windows_path = unc_path.replace('/', '\\')
            if not windows_path.startswith('\\\\'):
                windows_path = '\\\\' + windows_path.lstrip('\\')
            
            # 讀取檔案
            with open(windows_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 讀取前 20 行
                first_lines = []
                for i, line in enumerate(f):
                    if i >= 20:
                        break
                    first_lines.append(line)
                
                # 讀取最後 20 行 (需要重新遍歷或使用 seek)
                # 為了效率，使用 collections.deque
                from collections import deque
                f.seek(0)
                last_lines = deque(f, maxlen=20)
            
            # 合併並解析座標
            all_lines = first_lines + list(last_lines)
            first_coord = None
            last_coord = None
            
            for line in all_lines:
                coord = self._parse_single_xyz_line(line)
                if coord:
                    if first_coord is None:
                        first_coord = coord
                    last_coord = coord
            
            if first_coord and last_coord:
                # 計算中心點
                avg_lat = (first_coord['lat'] + last_coord['lat']) / 2
                avg_lng = (first_coord['lng'] + last_coord['lng']) / 2
                return {'lat': avg_lat, 'lng': avg_lng}
            elif first_coord:
                return first_coord
            
            return None
            
        except FileNotFoundError:
            logger.debug(f'無法找到檔案: {unc_path}')
            return None
        except PermissionError:
            logger.debug(f'無權限讀取: {unc_path}')
            return None
        except Exception as e:
            logger.debug(f'讀取檔案失敗 {unc_path}: {e}')
            return None

    def _parse_single_xyz_line(self, line: str) -> dict:
        """
        解析單行 XYZ 座標
        
        格式: X Y Z (空白分隔) 或 X,Y,Z (逗號分隔)
        
        Returns:
            {'lat': float, 'lng': float} 或 None
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # 分割：空白或逗號
        parts = re.split(r'[,\s]+', line)
        if len(parts) < 2:
            return None
        
        try:
            x = float(parts[0])
            y = float(parts[1])
            
            # 判斷座標系統
            if self._is_twd97(x, y):
                return self._twd97_to_wgs84(x, y)
            elif -180 <= x <= 180 and -90 <= y <= 90:
                # WGS84 (經度, 緯度)
                return {'lat': y, 'lng': x}
            elif -90 <= x <= 90 and -180 <= y <= 180:
                # WGS84 (緯度, 經度)
                return {'lat': x, 'lng': y}
        except ValueError:
            pass
        
        return None

    def _extract_location(self, source: dict) -> dict:
        """
        從文件資料中提取座標

        嘗試順序：
        1. 從 metadata 中的座標欄位
        2. 從路徑/標題解析地名進行地理編碼
        3. 從 content 中嘗試解析座標
        4. 從檔名解析 1:5000 圖號 (準確度較低，作為最後手段)

        Args:
            source: OpenSearch 文件 _source 資料

        Returns:
            {'lat': float, 'lng': float} 或 None
        """
        # 方法 1: 從 metadata 欄位取得座標
        if source.get('location'):
            loc = source['location']
            if isinstance(loc, dict) and 'lat' in loc and 'lon' in loc:
                return {'lat': float(loc['lat']), 'lng': float(loc['lon'])}

        # 取得檔名與路徑
        filename = (
            source.get('file', {}).get('filename') or
            source.get('filename') or
            os.path.basename(source.get('path', {}).get('real', ''))
        )
        
        full_path = source.get('path', {}).get('real', '') if isinstance(source.get('path'), dict) else ''

        # 方法 2: 從路徑中解析地名進行地理編碼
        # 嘗試找到台灣地名（縣市、鄉鎮、知名地點）
        coord = self._geocode_from_path(full_path)
        if coord:
            return coord

        # 方法 3: 從 content 解析第一個座標點 (若有)
        content = source.get('content', '')
        if content:
            coord = self._parse_xyz_content(content)
            if coord:
                return coord

        # 方法 4: 從 meta 欄位中尋找座標資訊
        meta = source.get('meta', '')
        if meta:
            coord = self._parse_coordinates_from_text(meta)
            if coord:
                return coord

        # 方法 5 (最後手段): 從檔名解析 1:5000 圖號
        # 注意：此方法準確度較低，僅在其他方法都失敗時使用
        if filename:
            coord = self._parse_sheet_number(filename)
            if coord:
                return coord

            coord = self._parse_twd97_from_filename(filename)
            if coord:
                return coord

        return None

    def _geocode_from_path(self, path: str) -> dict:
        """
        從檔案路徑中識別台灣地名並進行地理編碼
        
        例如: /花東地區鐵路雙軌化工程(花蓮工程處)/ -> 花蓮
        """
        if not path:
            return None
        
        # 常見的台灣地名對照表（東部地區優先，因為 DTM 常見於鐵路工程）
        location_keywords = {
            # 花東鐵路相關
            '花蓮': {'lat': 23.9910, 'lng': 121.6111},
            '知本': {'lat': 22.7050, 'lng': 121.0410},
            '台東': {'lat': 22.7583, 'lng': 121.1444},
            '臺東': {'lat': 22.7583, 'lng': 121.1444},
            '玉里': {'lat': 23.3333, 'lng': 121.3167},
            '瑞穗': {'lat': 23.4972, 'lng': 121.3750},
            '光復': {'lat': 23.6703, 'lng': 121.4264},
            '鳳林': {'lat': 23.7458, 'lng': 121.4533},
            '壽豐': {'lat': 23.8686, 'lng': 121.5103},
            '吉安': {'lat': 23.9628, 'lng': 121.5631},
            '新城': {'lat': 24.1281, 'lng': 121.6508},
            '太魯閣': {'lat': 24.1575, 'lng': 121.6211},
            '蘇澳': {'lat': 24.5953, 'lng': 121.8522},
            '南澳': {'lat': 24.4653, 'lng': 121.7992},
            '宜蘭': {'lat': 24.7570, 'lng': 121.7533},
            # 西部主要城市
            '台北': {'lat': 25.0330, 'lng': 121.5654},
            '臺北': {'lat': 25.0330, 'lng': 121.5654},
            '桃園': {'lat': 24.9936, 'lng': 121.3010},
            '新竹': {'lat': 24.8017, 'lng': 120.9714},
            '苗栗': {'lat': 24.5602, 'lng': 120.8214},
            '台中': {'lat': 24.1477, 'lng': 120.6736},
            '臺中': {'lat': 24.1477, 'lng': 120.6736},
            '彰化': {'lat': 24.0752, 'lng': 120.5389},
            '雲林': {'lat': 23.7092, 'lng': 120.4313},
            '嘉義': {'lat': 23.4801, 'lng': 120.4491},
            '台南': {'lat': 22.9999, 'lng': 120.2269},
            '臺南': {'lat': 22.9999, 'lng': 120.2269},
            '高雄': {'lat': 22.6273, 'lng': 120.3014},
            '屏東': {'lat': 22.6762, 'lng': 120.4929},
        }
        
        found_locations = []
        
        for keyword, coord in location_keywords.items():
            if keyword in path:
                found_locations.append((path.find(keyword), coord))
        
        if not found_locations:
            return None
        
        if len(found_locations) == 1:
            return found_locations[0][1]
        
        # 如果找到多個地名（如「花蓮~知本」），計算中點
        if len(found_locations) >= 2:
            # 按出現位置排序
            found_locations.sort(key=lambda x: x[0])
            
            # 取前兩個地點的中點
            loc1 = found_locations[0][1]
            loc2 = found_locations[-1][1]
            
            avg_lat = (loc1['lat'] + loc2['lat']) / 2
            avg_lng = (loc1['lng'] + loc2['lng']) / 2
            
            return {'lat': avg_lat, 'lng': avg_lng}
        
        return None

    def _parse_sheet_number(self, filename: str) -> dict:
        """
        從檔名解析台灣 1:5000 圖號

        格式如: 96183013OH.xyz, 94194059.xyz
        圖號為 8 位數字
        """
        # 移除副檔名
        name = os.path.splitext(filename)[0]

        # 尋找 8 位數字的圖號
        match = re.search(r'(\d{8})', name)
        if match:
            sheet_no = match.group(1)
            result = self.MapGridService.decode_1_5000_sheet(sheet_no)
            if result:
                lat, lng = result
                return {'lat': lat, 'lng': lng}

        return None

    def _parse_twd97_from_filename(self, filename: str) -> dict:
        """
        從檔名解析 TWD97 座標

        常見格式:
        - 123456_2345678.xyz
        - X123456Y2345678.xyz
        - tile_123456_2345678.xyz
        """
        # 移除副檔名
        name = os.path.splitext(filename)[0]

        # 模式 1: 數字_數字
        match = re.search(r'(\d{6})_(\d{7})', name)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            if self._is_twd97(x, y):
                return self._twd97_to_wgs84(x, y)

        # 模式 2: X數字Y數字
        match = re.search(r'[xX](\d{6})[yY](\d{7})', name)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            if self._is_twd97(x, y):
                return self._twd97_to_wgs84(x, y)

        # 模式 3: 連續 13 位數字 (先 6 位 X，後 7 位 Y)
        match = re.search(r'(\d{13})', name)
        if match:
            digits = match.group(1)
            x, y = int(digits[:6]), int(digits[6:])
            if self._is_twd97(x, y):
                return self._twd97_to_wgs84(x, y)

        return None

    def _parse_xyz_content(self, content: str, max_lines: int = 100) -> dict:
        """
        解析 XYZ 內容並回傳中心點座標

        Args:
            content: XYZ 檔案內容
            max_lines: 最多解析行數

        Returns:
            中心點座標 {'lat': float, 'lng': float} 或 None
        """
        lines = content.strip().split('\n')[:max_lines]
        points = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # 分割：空白或逗號
            parts = re.split(r'[,\s]+', line)
            if len(parts) >= 2:
                try:
                    x = float(parts[0])
                    y = float(parts[1])

                    # 判斷座標系統
                    if self._is_twd97(x, y):
                        coord = self._twd97_to_wgs84(x, y)
                        if coord:
                            points.append(coord)
                    elif -180 <= x <= 180 and -90 <= y <= 90:
                        # 可能是 WGS84 (經度, 緯度)
                        points.append({'lat': y, 'lng': x})
                    elif -90 <= x <= 90 and -180 <= y <= 180:
                        # 可能是 WGS84 (緯度, 經度)
                        points.append({'lat': x, 'lng': y})
                except ValueError:
                    continue

        if not points:
            return None

        # 計算中心點
        avg_lat = sum(p['lat'] for p in points) / len(points)
        avg_lng = sum(p['lng'] for p in points) / len(points)

        return {'lat': avg_lat, 'lng': avg_lng}

    def _parse_coordinates_from_text(self, text: str) -> dict:
        """
        從文字中嘗試提取座標資訊
        """
        # 嘗試匹配經緯度格式
        # 格式: 121.5, 25.0 或 121.5°E, 25.0°N
        lat_match = re.search(r'(\d{2}(?:\.\d+)?)\s*°?\s*[nN北]', text)
        lng_match = re.search(r'(\d{2,3}(?:\.\d+)?)\s*°?\s*[eE東]', text)

        if lat_match and lng_match:
            return {
                'lat': float(lat_match.group(1)),
                'lng': float(lng_match.group(1))
            }

        # 嘗試匹配 TWD97 座標
        twd_match = re.search(r'[xXeE]\s*[:=]?\s*(\d{6})\s*[,，]\s*[yYnN]\s*[:=]?\s*(\d{7})', text)
        if twd_match:
            x, y = int(twd_match.group(1)), int(twd_match.group(2))
            if self._is_twd97(x, y):
                return self._twd97_to_wgs84(x, y)

        return None

    def _is_twd97(self, x: float, y: float) -> bool:
        """
        判斷座標是否為 TWD97 座標系統
        """
        return (
            self.TWD97_X_MIN <= x <= self.TWD97_X_MAX and
            self.TWD97_Y_MIN <= y <= self.TWD97_Y_MAX
        )

    def _twd97_to_wgs84(self, x: float, y: float) -> dict:
        """
        將 TWD97 座標轉換為 WGS84 經緯度

        使用簡化的近似轉換公式
        精確轉換需要使用 pyproj 等專業套件

        Args:
            x: TWD97 X 座標 (東距)
            y: TWD97 Y 座標 (北距)

        Returns:
            {'lat': float, 'lng': float}
        """
        # TWD97 參數
        # 中央經線: 121°E
        # 中央緯度: 0°
        # 東偏移: 250000m
        # 北偏移: 0m

        # 簡化轉換公式 (近似值，誤差約 10-50m)
        # 這是一個線性近似，適用於台灣區域
        x0 = 250000  # 中央經線偏移
        k0 = 0.9999  # 縮放因子

        # 近似轉換
        lng = 121.0 + (x - x0) / 111320 / k0
        lat = y / 110540

        # 驗證結果在合理範圍內 (台灣區域)
        if 119 <= lng <= 123 and 21 <= lat <= 26:
            return {'lat': lat, 'lng': lng}

        return None
