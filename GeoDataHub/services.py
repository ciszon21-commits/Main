"""
GeoDataHub Services
====================
地理服務模組，包含：
- Nominatim 地址轉座標服務
- 地理空間查詢服務
- OpenSearch 地理整合
"""

import requests
import time
from typing import Optional, Dict, List, Tuple
from django.conf import settings
from django.db.models import Q
from decimal import Decimal

try:
    from GeoCoding.services import get_geocoding_service
except ImportError:
    get_geocoding_service = None


class GeocodingService:
    """
    地址轉座標服務 - 使用 Nominatim (OpenStreetMap)
    
    支援：
    - 中文地址轉座標
    - 座標轉地址 (反向地理編碼)
    - 批次轉換 (遵守速率限制)
    """
    
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    
    # 速率限制：每秒最多 1 次請求
    RATE_LIMIT_SECONDS = 1.1  # Slightly more than 1 second to be safe
    _last_request_time = 0.0

    def __init__(self):
        self.session = requests.Session()
        # OSM requires a valid, unique User-Agent with contact info
        self.session.headers.update({
            'User-Agent': 'CoDevStudio/1.0 (codevstudio@local.dev)',
            'Referer': 'http://localhost:8000',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept': 'application/json'
        })
        
        # 預設邊界：台灣 (wider bounds for better coverage)
        self.default_bounds = getattr(settings, 'GEOCODING_DEFAULT_BOUNDS', {
            'north': 26.5,
            'south': 21.5,
            'east': 123.0,
            'west': 119.0,
        })

        self.internal_geocoder = None
        if get_geocoding_service:
            try:
                self.internal_geocoder = get_geocoding_service()
            except Exception as exc:
                print(f'[GeoDataHub] Local GeoCoding service unavailable: {exc}')

    def _rate_limit(self):
        """遵守 Nominatim 速率限制"""
        now = time.time()
        elapsed = now - GeocodingService._last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        GeocodingService._last_request_time = time.time()

    def _geocode_internal(self, address: str) -> Optional[Dict]:
        """優先使用 GeoCoding app 的本地地名資料"""
        if not self.internal_geocoder or not address:
            return None
        try:
            result = self.internal_geocoder.geocode(address, save_history=False)
        except Exception as exc:
            print(f'[GeoDataHub] GeoCoding geocoder error: {exc}')
            return None

        if not result or not getattr(result, 'success', False):
            return None

        lat = getattr(result, 'latitude', None)
        lng = getattr(result, 'longitude', None)
        if lat is None or lng is None:
            return None

        county = getattr(result, 'county', None)
        township = getattr(result, 'township', None)
        village = getattr(result, 'village', None)

        address_dict = {}
        if county:
            address_dict['county'] = county
        if township:
            address_dict['township'] = township
        if village:
            address_dict['village'] = village

        if hasattr(result, 'full_address') and result.full_address:
            display_name = result.full_address
        else:
            display_name = ''.join(part for part in [county, township, village] if part) or address

        confidence = getattr(result, 'confidence', 0.0) or 0.0

        return {
            'latitude': float(lat),
            'longitude': float(lng),
            'display_name': display_name,
            'address': address_dict,
            'confidence': float(confidence),
            'source': 'GeoCoding'
        }

    def geocode_address(
        self, 
        address: str, 
        country: str = 'TW',
        bounded: bool = True
    ) -> Optional[Dict]:
        """
        將地址轉換為座標 (優先使用快取且具備失敗保護)
        """
        from .models import GeocodingCache
        from django.utils import timezone
        
        # 1. 檢查本地快取
        cache_entry, created = GeocodingCache.objects.get_or_create(query=address)
        
        if cache_entry.is_success and cache_entry.result:
            return cache_entry.result
            
        country_code = (country or 'TW').upper()

        if country_code == 'TW':
            local_result = self._geocode_internal(address)
            if local_result:
                cache_entry.result = local_result
                cache_entry.is_success = True
                cache_entry.fail_count = 0
                cache_entry.save()
                return local_result
            
        # 2. 失敗保護：如果失敗超過 3 次且最近嘗試過，則跳過
        if not cache_entry.is_success and cache_entry.fail_count >= 3:
            # 如果是最近一小時內的嘗試，則直接跳過外部請求
            if (timezone.now() - cache_entry.last_attempt).total_seconds() < 3600:
                return None
        
        # 3. 執行外部請求
        result = None
        
        # For Taiwan addresses, try multiple services starting with ArcGIS which is reliable
        if country_code == 'TW':
            # 1. Try ArcGIS (Most reliable for Taiwan detail addresses currently)
            result = self._geocode_arcgis(address)
            
            # 2. Try TGOS (Taiwan Government Open Service) fallback if ArcGIS failed
            if not result:
                result = self._geocode_tgos(address)
        
        # Fallback to Nominatim if others failed
        if not result:
            result = self._geocode_nominatim(address, country_code, bounded)
            
        # 4. 更新快取狀態
        if result:
            cache_entry.result = result
            cache_entry.is_success = True
            cache_entry.fail_count = 0
            cache_entry.save()
        else:
            cache_entry.fail_count += 1
            cache_entry.is_success = False
            cache_entry.save()
            
        return result
    
    def _geocode_arcgis(self, address: str) -> Optional[Dict]:
        """使用 ArcGIS World Geocoding Service"""
        try:
            url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
            params = {
                'f': 'json',
                'singleLine': address,
                'maxLocations': 1,
                'outFields': 'Addr_type,Match_addr,StAddr,City'
            }
            # No rate limit check needed for low volume ArcGIS usage
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'candidates' in data and len(data['candidates']) > 0:
                best = data['candidates'][0]
                return {
                    'latitude': float(best['location']['y']),
                    'longitude': float(best['location']['x']),
                    'display_name': best.get('address', address),
                    'address': {
                        'road': best.get('attributes', {}).get('StAddr', ''), 
                        'city': best.get('attributes', {}).get('City', '')
                    },
                    'confidence': float(best.get('score', 0)) / 100.0,
                    'source': 'ArcGIS'
                }
            return None
        except (requests.ConnectionError, requests.Timeout) as e:
            # ArcGIS connection issues - silent failure
            return None
        except requests.RequestException as e:
            # ArcGIS is generally stable, but silence common network issues
            if not (e.response is not None and e.response.status_code in [503, 404]):
                print(f"ArcGIS geocoding error: {e}")
            return None
        except Exception as e:
            print(f"ArcGIS unexpected error: {e}")
            return None

    def _geocode_tgos(self, address: str) -> Optional[Dict]:
        """使用 NLSC (內政部國土測繪中心) 地址定位服務"""
        try:
            # NLSC 提供的開放 API
            url = "https://api.nlsc.gov.tw/other/TGLocator/TGLocator.asmx/QueryAddr"
            params = {
                'oAPPId': '',  # Public access
                'oAPIKey': '',  # Public access
                'oAddress': address,
                'oSRS': 'EPSG:4326',
                'oFuzzyType': '2',  # Fuzzy matching
                'oResultDataType': 'JSON'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and 'AddressList' in data and len(data['AddressList']) > 0:
                best = data['AddressList'][0]
                return {
                    'latitude': float(best.get('Y', 0)),
                    'longitude': float(best.get('X', 0)),
                    'display_name': best.get('FULL_ADDR', address),
                    'address': {'road': best.get('ROAD', ''), 'city': best.get('COUNTY', '')},
                    'confidence': 0.9,
                    'source': 'TGOS'
                }
            return None
        except (requests.ConnectionError, requests.Timeout) as e:
            # TGOS connection issues - silent failure
            return None
        except requests.RequestException as e:
            # TGOS is known to have 404/503 issues, silence them
            if not (e.response is not None and e.response.status_code in [503, 404]):
                print(f"TGOS geocoding error: {e}")
            return None
        except Exception as e:
            print(f"TGOS unexpected error: {e}")
            return None
    
    def _geocode_nominatim(
        self, 
        address: str, 
        country: str = 'TW',
        bounded: bool = True
    ) -> Optional[Dict]:
        """使用 Nominatim (OpenStreetMap) 地址定位"""
        self._rate_limit()
        
        params = {
            'q': address,
            'format': 'json',
            'addressdetails': 1,
            'limit': 5,
        }
        
        if country:
            params['countrycodes'] = country.lower()
        
        if bounded and self.default_bounds:
            params['viewbox'] = (
                f"{self.default_bounds['west']},{self.default_bounds['north']},"
                f"{self.default_bounds['east']},{self.default_bounds['south']}"
            )
        
        try:
            response = self.session.get(
                f"{self.NOMINATIM_BASE_URL}/search",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = max(results, key=lambda x: float(x.get('importance', 0)))
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'display_name': result.get('display_name', ''),
                    'address': result.get('address', {}),
                    'confidence': self._calculate_confidence(result),
                    'source': 'Nominatim'
                }
            return None
            
        except (requests.ConnectionError, requests.Timeout) as e:
            # Nominatim connection issues - silent failure
            return None
        except requests.RequestException as e:
            # Nominatim often returns 503 when over rate limit, silence it
            if not (e.response is not None and e.response.status_code in [503, 429]):
                print(f"Nominatim geocoding error: {e}")
            return None
        except Exception as e:
            print(f"Nominatim unexpected error: {e}")
            return None



    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict]:
        """
        將座標轉換為地址 (反向地理編碼)
        
        Args:
            lat: 緯度
            lng: 經度
            
        Returns:
            {
                'display_name': str,
                'address': dict,
                'city': str,
                'district': str,
                'country': str
            }
            或 None 如果找不到
        """
        self._rate_limit()
        
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18  # 最高精度
        }
        
        try:
            response = self.session.get(
                f"{self.NOMINATIM_BASE_URL}/reverse",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            if result and 'error' not in result:
                address = result.get('address', {})
                return {
                    'display_name': result.get('display_name', ''),
                    'address': address,
                    'city': address.get('city') or address.get('town') or address.get('county', ''),
                    'district': address.get('suburb') or address.get('district', ''),
                    'country': address.get('country', ''),
                }
            return None
            
        except requests.RequestException as e:
            print(f"Reverse geocoding error: {e}")
            return None

    def batch_geocode(
        self, 
        addresses: List[str], 
        country: str = 'TW'
    ) -> List[Optional[Dict]]:
        """
        批次地址轉換 (會自動遵守速率限制)
        
        Args:
            addresses: 地址列表
            country: 國家代碼
            
        Returns:
            結果列表，順序與輸入相同
        """
        results = []
        for address in addresses:
            result = self.geocode_address(address, country)
            results.append(result)
        return results

    def _calculate_confidence(self, result: dict) -> float:
        """計算地理編碼信心度"""
        # 基於 Nominatim 的 importance 和 class
        importance = float(result.get('importance', 0.5))
        
        # 類型權重
        osm_type = result.get('type', '')
        type_weights = {
            'building': 1.0,
            'house': 0.95,
            'street': 0.8,
            'residential': 0.75,
            'suburb': 0.6,
            'city': 0.5,
            'county': 0.4,
        }
        type_weight = type_weights.get(osm_type, 0.7)
        
        return min(1.0, importance * type_weight)


class GeoQueryService:
    """
    地理空間查詢服務
    支援在 Django ORM 中進行地理查詢
    """
    
    def __init__(self):
        from .models import GeoDataSource, GeoLocation
        self.GeoDataSource = GeoDataSource
        self.GeoLocation = GeoLocation

    def search_by_bounds(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        category_id: Optional[int] = None,
        keyword: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict:
        """
        在指定邊界框內搜尋資料
        
        Args:
            north, south, east, west: 邊界座標
            category_id: 分類 ID (可選)
            keyword: 關鍵字 (可選)
            source_type: 來源類型 (可選)
            limit: 結果數量限制
            
        Returns:
            {
                'count': int,
                'results': QuerySet
            }
        """
        # 基本查詢：有位置資訊且在範圍內
        queryset = self.GeoDataSource.objects.filter(
            location__isnull=False,
            is_visible=True,
            location__latitude__gte=Decimal(str(south)),
            location__latitude__lte=Decimal(str(north)),
            location__longitude__gte=Decimal(str(west)),
            location__longitude__lte=Decimal(str(east))
        ).select_related('location', 'category', 'created_by')
        
        # 分類篩選
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 來源類型篩選
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # 關鍵字搜尋
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(location__address__icontains=keyword)
            )
        
        count = queryset.count()
        results = queryset[:limit]
        
        return {
            'count': count,
            'results': results
        }

    def search_by_radius(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float,
        category_id: Optional[int] = None,
        keyword: Optional[str] = None,
        limit: int = 100
    ) -> Dict:
        """
        在指定半徑內搜尋資料 (近似計算)
        
        注意：這是一個近似計算，使用邊界框作為初步篩選
        精確距離計算需要 PostGIS 或其他地理擴展
        """
        # 近似計算邊界框
        # 1 度緯度 ≈ 111 km
        # 1 度經度 ≈ 111 km * cos(緯度)
        import math
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        return self.search_by_bounds(
            north=center_lat + lat_delta,
            south=center_lat - lat_delta,
            east=center_lng + lng_delta,
            west=center_lng - lng_delta,
            category_id=category_id,
            keyword=keyword,
            limit=limit
        )

    def count_by_area(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        category_id: Optional[int] = None
    ) -> int:
        """計算區域內的資料數量"""
        result = self.search_by_bounds(
            north=north, south=south, east=east, west=west,
            category_id=category_id,
            limit=0
        )
        return result['count']

    def get_categories_with_counts(self, bounds: Optional[Dict] = None) -> List[Dict]:
        """取得分類列表及各分類的資料數量"""
        from .models import GeoCategory
        from django.db.models import Count
        
        categories = GeoCategory.objects.filter(is_active=True)
        
        result = []
        for cat in categories:
            if bounds:
                count = self.count_by_area(
                    north=bounds['north'],
                    south=bounds['south'],
                    east=bounds['east'],
                    west=bounds['west'],
                    category_id=cat.id
                )
            else:
                count = self.GeoDataSource.objects.filter(
                    category=cat,
                    is_visible=True,
                    location__isnull=False
                ).count()
            
            result.append({
                'id': cat.id,
                'name': cat.name,
                'icon': cat.icon,
                'color': cat.color,
                'count': count
            })
        
        return result


class OpenSearchGeoService:
    """
    OpenSearch 地理整合服務
    擴展現有 OpenSearch 服務以支援地理查詢
    """
    
    def __init__(self):
        # 重用現有的 OpenSearch 服務
        try:
            from OpenSearch.services import get_client
            self.get_client = get_client
        except ImportError:
            self.get_client = None
            print("Warning: OpenSearch services not available")

    def geo_bounding_box_search(
        self,
        query: str = "",
        indices: str = "*",
        bounds: Optional[Dict] = None,
        geo_field: str = "location",
        size: int = 100,
        from_: int = 0
    ) -> Dict:
        """
        在指定邊界框內執行 OpenSearch 搜尋
        
        Args:
            query: 搜尋關鍵字
            indices: 索引模式
            bounds: {'top_left': {'lat': float, 'lon': float}, 'bottom_right': {...}}
            geo_field: 地理欄位名稱
            size: 結果數量
            from_: 起始位置
            
        Returns:
            OpenSearch 搜尋結果
        """
        if not self.get_client:
            return {"error": "OpenSearch not configured", "hits": {"hits": [], "total": {"value": 0}}}
        
        client = self.get_client()
        
        # 建構查詢
        must_clause = []
        filter_clause = []
        
        # 關鍵字查詢
        if query:
            must_clause.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content^2", "file^2", "path", "meta", "*"],
                    "type": "phrase"
                }
            })
        else:
            must_clause.append({"match_all": {}})
        
        # 地理邊界框篩選
        if bounds:
            filter_clause.append({
                "geo_bounding_box": {
                    geo_field: {
                        "top_left": bounds.get('top_left', {}),
                        "bottom_right": bounds.get('bottom_right', {})
                    }
                }
            })
        
        body = {
            "query": {
                "bool": {
                    "must": must_clause,
                    "filter": filter_clause
                }
            },
            "size": size,
            "from": from_
        }
        
        try:
            # 處理索引別名
            if indices == "*":
                search_indices = "alias_*,reviewing_*"
            else:
                parts = [p.strip() for p in indices.split(',')]
                alias_parts = []
                for part in parts:
                    if not part.startswith('alias_') and not part.startswith('reviewing_'):
                        alias_parts.append(f'alias_{part}')
                        alias_parts.append(f'reviewing_{part}')
                    else:
                        alias_parts.append(part)
                search_indices = ','.join(alias_parts)
            
            response = client.search(
                index=search_indices,
                body=body,
                ignore_unavailable=True,
                request_timeout=60
            )
            return response
        except Exception as e:
            return {"error": str(e), "hits": {"hits": [], "total": {"value": 0}}}

    def geo_distance_search(
        self,
        query: str = "",
        indices: str = "*",
        center: Optional[Tuple[float, float]] = None,
        distance: str = "10km",
        geo_field: str = "location",
        size: int = 100
    ) -> Dict:
        """
        在指定距離內執行 OpenSearch 搜尋
        
        Args:
            query: 搜尋關鍵字
            indices: 索引模式
            center: (lat, lng) 中心點
            distance: 距離，例如 "10km"
            geo_field: 地理欄位名稱
            size: 結果數量
        """
        if not self.get_client or not center:
            return {"error": "OpenSearch not configured or center not provided", 
                    "hits": {"hits": [], "total": {"value": 0}}}
        
        client = self.get_client()
        
        must_clause = []
        filter_clause = []
        
        if query:
            must_clause.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content^2", "*"]
                }
            })
        else:
            must_clause.append({"match_all": {}})
        
        # 距離篩選
        filter_clause.append({
            "geo_distance": {
                "distance": distance,
                geo_field: {
                    "lat": center[0],
                    "lon": center[1]
                }
            }
        })
        
        body = {
            "query": {
                "bool": {
                    "must": must_clause,
                    "filter": filter_clause
                }
            },
            "size": size,
            "sort": [
                {
                    "_geo_distance": {
                        geo_field: {
                            "lat": center[0],
                            "lon": center[1]
                        },
                        "order": "asc",
                        "unit": "km"
                    }
                }
            ]
        }
        
        try:
            response = client.search(
                index="alias_*,reviewing_*" if indices == "*" else indices,
                body=body,
                ignore_unavailable=True,
                request_timeout=60
            )
            return response
        except Exception as e:
            return {"error": str(e), "hits": {"hits": [], "total": {"value": 0}}}

    def geo_aggregation(
        self,
        indices: str = "*",
        geo_field: str = "location",
        precision: int = 5
    ) -> Dict:
        """
        按 GeoHash 聚合資料統計
        
        Args:
            indices: 索引模式
            geo_field: 地理欄位名稱
            precision: GeoHash 精度 (1-12)
        """
        if not self.get_client:
            return {"error": "OpenSearch not configured", "aggregations": {}}
        
        client = self.get_client()
        
        body = {
            "size": 0,
            "aggs": {
                "geo_grid": {
                    "geohash_grid": {
                        "field": geo_field,
                        "precision": precision
                    }
                }
            }
        }
        
        try:
            response = client.search(
                index="alias_*,reviewing_*" if indices == "*" else indices,
                body=body,
                ignore_unavailable=True
            )
            return response
        except Exception as e:
            return {"error": str(e), "aggregations": {}}


class MapGridService:
    """
    台灣地圖網格解碼服務
    支援：
    - 1:5,000 像片基本圖圖號 (8位數字，如 94194059)
    - 1:25,000 精選圖號 (如 78A)
    """

    @staticmethod
    def decode_1_5000_sheet(sheet_no: str) -> Optional[Tuple[float, float]]:
        """
        將 1:5,000 圖號轉換成經緯度 (中心點)
        格式：XXYY ABCD
        XX, YY: 1:100,000 圖幅編號
        ABCD: 1:5,000 之分割編號
        
        這是一個簡化的實作，基於台灣常見的圖號規則。
        1:5,000 圖號中心點約略計算方式。
        """
        if not sheet_no or len(sheet_no) < 8 or not sheet_no.isdigit():
            return None
            
        try:
            # 範例：94194059
            # 前四碼大多與 TWD97/TM2 座標原點有關
            # 這裡使用一個近似的線性映射邏輯
            # 註：精確轉換需要對應的圖幅索引表
            
            # 台灣 1:5,000 圖幅通常橫跨 2.5' 經度, 1.5' 緯度
            # 這裡使用 heuristic 方式找出大概位置
            
            # 第一二碼：經度相關 (94 -> 120.x)
            # 第三四碼：緯度相關 (19 -> 23.x)
            x_idx = int(sheet_no[0:2])
            y_idx = int(sheet_no[2:4])
            
            # 近似中央經緯度 (基於觀察到的樣本如 94194059 -> 龍蛟潭 23.3, 120.2)
            # 這是一個經驗公式，可能需要根據更多樣本調整
            base_lng = 114.0 + (x_idx * 0.066)
            base_lat = 22.0 + (y_idx * 0.066)
            
            # 後四碼是更細的劃分
            sub_x = int(sheet_no[4:6])
            sub_y = int(sheet_no[6:8])
            
            lng = base_lng + (sub_x * 0.005)
            lat = base_lat + (sub_y * 0.005)
            
            return lat, lng
        except:
            return None

    @staticmethod
    def decode_any_code(code: str) -> Optional[Tuple[float, float]]:
        """智慧識別各類編碼並嘗試解碼"""
        if not code:
            return None
            
        code = code.strip().upper()
        
        # 1. 1:5,000 圖號 (8位純數字)
        if len(code) == 8 and code.isdigit():
            return MapGridService.decode_1_5000_sheet(code)
            
        # 2. 1:25,000 圖號 (如 78A, 78B)
        # TODO: 實作 1:25k 解碼邏輯
        
        return None


class OpenSearchMappingService:
    """
    OpenSearch 資料與 GeoDataHub 的映射與同步服務
    """
    
    def __init__(self):
        from .models import GeoDataSource, GeoCategory, GeoLocation, GeoSyncLog
        from OpenSearch.services import get_client
        self.GeoDataSource = GeoDataSource
        self.GeoCategory = GeoCategory
        self.GeoLocation = GeoLocation
        self.GeoSyncLog = GeoSyncLog
        self.get_client = get_client
        self.geocoder = GeocodingService()
        self.grid_service = MapGridService()

    def sync_sino_maps_two_stage(self, mode='full', limit=0, batch_size=100) -> Dict:
        """
        兩階段大規模同步：
        mode='metadata': 僅擷取 OpenSearch 資料，不進行地理編碼
        mode='location': 針對資料庫中位置為空的項目進行地理編碼解析
        mode='full': 循序執行兩階段
        """
        results = {}
        
        if mode in ['metadata', 'full']:
            results['metadata_stage'] = self._stage_metadata_sync(limit, batch_size)
            
        if mode in ['location', 'full']:
            # 即使第一階段沒跑，也可以單獨跑位置解析
            results['location_stage'] = self._stage_location_resolve(limit, batch_size)
            
        return results

    def _stage_metadata_sync(self, limit=0, batch_size=100) -> Dict:
        """第一階段：從 OpenSearch 快速擷取元數據"""
        from opensearchpy.helpers import scan
        from django.db import transaction
        from django.utils import timezone
        import logging
        logger = logging.getLogger(__name__)

        # 建立日誌
        sync_log = self.GeoSyncLog.objects.create(
            task_type=self.GeoSyncLog.TaskType.METADATA_SYNC,
            status=self.GeoSyncLog.Status.RUNNING
        )

        try:
            client = self.get_client()
            category, _ = self.GeoCategory.objects.get_or_create(
                name="地理圖資",
                defaults={'icon': '🗺️', 'color': '#2E7D32'}
            )

            # 預載現有 ID
            existing_ids = set(self.GeoDataSource.objects.filter(
                opensearch_index='sino_map'
            ).values_list('opensearch_doc_id', flat=True))
            
            query = {'query': {'match_all': {}}}
            scanner = scan(
                client,
                index='sino_map',
                query=query,
                size=batch_size,
                scroll='15m',
                clear_scroll=False
            )

            new_items = []
            processed = 0
            created = 0
            skipped = 0
            
            for hit in scanner:
                processed += 1
                doc_id = hit['_id']
                
                if doc_id in existing_ids:
                    skipped += 1
                else:
                    source = hit['_source']
                    ds = self.GeoDataSource(
                        opensearch_index='sino_map',
                        opensearch_doc_id=doc_id,
                        title=source.get('title') or source.get('filename', '未命名圖資'),
                        description=source.get('content', ''),
                        source_type='opensearch',
                        category=category,
                        metadata=source,
                        is_visible=True
                    )
                    new_items.append(ds)
                    
                    if len(new_items) >= batch_size:
                        with transaction.atomic():
                            self.GeoDataSource.objects.bulk_create(new_items)
                        created += len(new_items)
                        new_items = []
                        sync_log.update_progress(processed=batch_size, created=batch_size)

                if limit and processed >= limit:
                    break

            if new_items:
                with transaction.atomic():
                    self.GeoDataSource.objects.bulk_create(new_items)
                created += len(new_items)
                sync_log.update_progress(processed=len(new_items), created=len(new_items))

            sync_log.status = self.GeoSyncLog.Status.SUCCESS
            sync_log.end_time = timezone.now()
            sync_log.save()
            
            return {'status': 'success', 'created': created, 'processed': processed}

        except Exception as e:
            sync_log.status = self.GeoSyncLog.Status.FAILED
            sync_log.error_message = str(e)
            sync_log.end_time = timezone.now()
            sync_log.save()
            logger.error(f"Metadata Sync Failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _stage_location_resolve(self, limit=0, batch_size=100) -> Dict:
        """第二階段：背景解析位置座標"""
        from django.db import transaction
        from django.utils import timezone
        import logging
        logger = logging.getLogger(__name__)

        sync_log = self.GeoSyncLog.objects.create(
            task_type=self.GeoSyncLog.TaskType.LOCATION_RESOLVE,
            status=self.GeoSyncLog.Status.RUNNING
        )

        try:
            # 找出尚未解析位置的資料 (限 OpenSearch 匯入的)
            pending_sources = self.GeoDataSource.objects.filter(
                location__isnull=True,
                opensearch_index='sino_map'
            )
            
            if limit:
                pending_sources = pending_sources[:limit]
            
            sync_log.total_expected = pending_sources.count()
            sync_log.save()

            processed = 0
            updated = 0
            errors = 0
            
            # 使用 iterator 減少記憶體消耗
            for ds in pending_sources.iterator(chunk_size=batch_size):
                processed += 1
                try:
                    location = self._resolve_location(ds.metadata)
                    if location:
                        ds.location = location
                        ds.save(update_fields=['location'])
                        updated += 1
                    
                    if processed % 10 == 0:
                        sync_log.update_progress(processed=10, updated=updated-sync_log.updated_count)
                        
                except Exception as e:
                    errors += 1
                    logger.warning(f"Failed to resolve location for {ds.id}: {e}")

            sync_log.status = self.GeoSyncLog.Status.SUCCESS
            sync_log.end_time = timezone.now()
            sync_log.save()
            
            return {'status': 'success', 'updated': updated, 'processed': processed}

        except Exception as e:
            sync_log.status = self.GeoSyncLog.Status.FAILED
            sync_log.error_message = str(e)
            sync_log.end_time = timezone.now()
            sync_log.save()
            return {'status': 'failed', 'error': str(e)}

    def sync_sino_maps(self, limit: int = 0, batch_size: int = 1000) -> Dict:
        """保留舊有的同步介面，但轉向兩階段實作"""
        return self.sync_sino_maps_two_stage(mode='full', limit=limit, batch_size=batch_size)

    def _resolve_location(self, source: dict):
        """嘗試從多種途徑解析位置"""
        # 1. 嘗試圖號解碼
        sheet_no = source.get('no')
        if sheet_no:
            coords = self.grid_service.decode_any_code(sheet_no)
            if coords:
                from .models import GeoLocation
                loc = GeoLocation.objects.create(
                    latitude=Decimal(str(coords[0])),
                    longitude=Decimal(str(coords[1])),
                    address=f"圖幅編號: {sheet_no}",
                    geometry_type='POINT'
                )
                return loc
                
        # 2. 嘗試標題地理編碼 (place name)
        title = source.get('title')
        if title and len(title) > 1:
            # 優先使用本地地名資料避免對外連線
            result = self.geocoder.geocode_address(title)
            if result and result.get('confidence', 0) > 0.6:
                from .models import GeoLocation
                address_meta = result.get('address') or {}
                loc = GeoLocation.objects.create(
                    latitude=Decimal(str(result['latitude'])),
                    longitude=Decimal(str(result['longitude'])),
                    address=result.get('display_name', title),
                    city=address_meta.get('city') or address_meta.get('county') or "",
                    district=(
                        address_meta.get('district')
                        or address_meta.get('township')
                        or address_meta.get('village')
                        or ""
                    ),
                    country=address_meta.get('country') or "台灣",
                    geometry_type='POINT',
                    accuracy=float(result.get('confidence', 0)) * 100
                )
                return loc
                
        return None


# 便捷函式
def geocode(address: str, country: str = 'TW') -> Optional[Dict]:
    """快速地址轉座標"""
    service = GeocodingService()
    return service.geocode_address(address, country)


def reverse_geocode(lat: float, lng: float) -> Optional[Dict]:
    """快速座標轉地址"""
    service = GeocodingService()
    return service.reverse_geocode(lat, lng)
