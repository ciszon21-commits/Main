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
    RATE_LIMIT_SECONDS = 1.0
    _last_request_time = 0.0

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoDataHub/1.0 (CoDevStudio; Contact: admin@example.com)',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
        })
        
        # 預設邊界：台灣
        self.default_bounds = getattr(settings, 'GEOCODING_DEFAULT_BOUNDS', {
            'north': 25.3,
            'south': 21.9,
            'east': 122.0,
            'west': 120.0,
        })

    def _rate_limit(self):
        """遵守 Nominatim 速率限制"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        GeocodingService._last_request_time = time.time()

    def geocode_address(
        self, 
        address: str, 
        country: str = 'TW',
        bounded: bool = True
    ) -> Optional[Dict]:
        """
        將地址轉換為座標
        
        Args:
            address: 地址字串 (支援中文)
            country: 國家代碼 (預設 TW)
            bounded: 是否限制在預設邊界內
            
        Returns:
            {
                'latitude': float,
                'longitude': float,
                'display_name': str,
                'address': dict,
                'confidence': float (0-1)
            }
            或 None 如果找不到
        """
        self._rate_limit()
        
        params = {
            'q': address,
            'format': 'json',
            'addressdetails': 1,
            'limit': 1,
        }
        
        # 加入國家限制
        if country:
            params['countrycodes'] = country.lower()
        
        # 加入邊界限制
        if bounded and self.default_bounds:
            params['bounded'] = 1
            params['viewbox'] = (
                f"{self.default_bounds['west']},{self.default_bounds['north']},"
                f"{self.default_bounds['east']},{self.default_bounds['south']}"
            )
        
        try:
            response = self.session.get(
                f"{self.NOMINATIM_BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = results[0]
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'display_name': result.get('display_name', ''),
                    'address': result.get('address', {}),
                    'confidence': self._calculate_confidence(result),
                    'raw': result
                }
            return None
            
        except requests.RequestException as e:
            print(f"Geocoding error: {e}")
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
                    is_visible=True
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


# 便捷函式
def geocode(address: str, country: str = 'TW') -> Optional[Dict]:
    """快速地址轉座標"""
    service = GeocodingService()
    return service.geocode_address(address, country)


def reverse_geocode(lat: float, lng: float) -> Optional[Dict]:
    """快速座標轉地址"""
    service = GeocodingService()
    return service.reverse_geocode(lat, lng)
