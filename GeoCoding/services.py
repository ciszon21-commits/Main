"""
地理編碼模糊比對服務
支援縣市、鄉鎮區、村里三層級的模糊比對
"""
import re
from difflib import SequenceMatcher, get_close_matches
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field

from django.db.models import Q

from .models import County, Township, Village, Landmark, GeoQuery


@dataclass
class GeoResult:
    """地理編碼結果"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    county: Optional[str] = None
    township: Optional[str] = None
    village: Optional[str] = None
    full_address: str = ""
    confidence: float = 0.0
    success: bool = False
    message: str = ""
    candidates: List[Dict[str, Any]] = field(default_factory=list)


class GeocodingService:
    """
    地理編碼服務
    
    支援多種輸入格式：
    - 完整地址: "台北市中山區中山里"
    - 部分地址: "中山區" 或 "中山里"
    - 模糊輸入: "台北中山" 或 "板橋"
    """
    
    # 縣市名稱標準化對照表 (包含簡稱、別稱等)
    COUNTY_ALIASES = {
        # 直轄市
        '台北': '臺北市', '台北市': '臺北市', '臺北': '臺北市', '北市': '臺北市',
        '新北': '新北市', '新北市': '新北市', '北縣': '新北市',
        '桃園': '桃園市', '桃園市': '桃園市', '桃市': '桃園市',
        '台中': '臺中市', '台中市': '臺中市', '臺中': '臺中市', '中市': '臺中市',
        '台南': '臺南市', '台南市': '臺南市', '臺南': '臺南市', '南市': '臺南市',
        '高雄': '高雄市', '高雄市': '高雄市', '雄市': '高雄市',
        # 省轄市
        '基隆': '基隆市', '基隆市': '基隆市',
        '新竹市': '新竹市', '竹市': '新竹市',
        '嘉義市': '嘉義市', '嘉市': '嘉義市',
        # 縣
        '新竹縣': '新竹縣', '竹縣': '新竹縣', '新竹': '新竹縣',  # 預設新竹為縣
        '苗栗': '苗栗縣', '苗栗縣': '苗栗縣',
        '彰化': '彰化縣', '彰化縣': '彰化縣',
        '南投': '南投縣', '南投縣': '南投縣',
        '雲林': '雲林縣', '雲林縣': '雲林縣',
        '嘉義縣': '嘉義縣', '嘉縣': '嘉義縣',
        '屏東': '屏東縣', '屏東縣': '屏東縣',
        '宜蘭': '宜蘭縣', '宜蘭縣': '宜蘭縣',
        '花蓮': '花蓮縣', '花蓮縣': '花蓮縣',
        '台東': '臺東縣', '台東縣': '臺東縣', '臺東': '臺東縣',
        '澎湖': '澎湖縣', '澎湖縣': '澎湖縣',
        '金門': '金門縣', '金門縣': '金門縣',
        '連江': '連江縣', '連江縣': '連江縣', '馬祖': '連江縣',
    }
    
    # 行政區後綴
    TOWNSHIP_SUFFIXES = ['區', '市', '鎮', '鄉']
    VILLAGE_SUFFIXES = ['里', '村']

    def __init__(self):
        self._county_cache = None
        self._township_cache = None
        self._village_cache = None
        self._landmark_cache = None
        self._all_names_cache = None

    def refresh_cache(self):
        """強制重新載入快取"""
        self._county_cache = None
        self._township_cache = None
        self._village_cache = None
        self._landmark_cache = None
        self._all_names_cache = None

    def _load_cache(self):
        """載入所有行政區資料快取"""
        if self._county_cache is None:
            self._county_cache = list(County.objects.all())
        if self._township_cache is None:
            self._township_cache = list(
                Township.objects.select_related('county').all()
            )
        if self._village_cache is None:
            self._village_cache = list(
                Village.objects.select_related('township', 'township__county').all()
            )
        if self._landmark_cache is None:
            self._landmark_cache = list(
                Landmark.objects.select_related('county', 'township').all()
            )

    def _build_search_index(self) -> Dict[str, List]:
        """建立搜尋索引"""
        self._load_cache()
        
        if self._all_names_cache:
            return self._all_names_cache
        
        self._all_names_cache = {
            'counties': [],
            'townships': [],
            'villages': [],
            'landmarks': []
        }
        
        for c in self._county_cache:
            self._all_names_cache['counties'].append({
                'name': c.name,
                'obj': c,
                'search_names': [c.name, c.name.replace('臺', '台')]
            })
        
        for t in self._township_cache:
            # 產生多種搜尋名稱變體
            search_names = [
                t.name,
                f"{t.county.name}{t.name}",
                t.county.name.replace('臺', '台') + t.name
            ]
            self._all_names_cache['townships'].append({
                'name': t.name,
                'full_name': f"{t.county.name}{t.name}",
                'obj': t,
                'search_names': search_names
            })
        
        for v in self._village_cache:
            search_names = [
                v.name,
                f"{v.township.name}{v.name}",
                f"{v.township.county.name}{v.township.name}{v.name}"
            ]
            self._all_names_cache['villages'].append({
                'name': v.name,
                'full_name': f"{v.township.county.name}{v.township.name}{v.name}",
                'obj': v,
                'search_names': search_names
            })
        
        for lm in self._landmark_cache:
            search_names = [lm.name, lm.name.replace('臺', '台')]
            # 加入別名
            for alias in lm.get_aliases_list():
                search_names.append(alias)
                search_names.append(alias.replace('臺', '台'))
            self._all_names_cache['landmarks'].append({
                'name': lm.name,
                'full_name': lm.name,
                'obj': lm,
                'search_names': search_names
            })
        
        return self._all_names_cache

    def _normalize_query(self, query: str) -> str:
        """標準化查詢字串"""
        # 移除多餘空白和標點
        query = re.sub(r'[\s,，、。．.·\-_]+', '', query)
        # 只移除門牌號碼格式的數字 (如: 123號, 5巷, 10弄)
        query = re.sub(r'\d+[號巷弄樓之F]+', '', query)
        # 移除路/街/段 後的內容 (詳細地址)
        query = re.sub(r'[路街段].+$', '', query)
        return query.strip()

    def _similarity(self, a: str, b: str) -> float:
        """計算兩字串的相似度 (0-1)"""
        if not a or not b:
            return 0.0
        # 標準化比較
        a_normalized = a.replace('臺', '台')
        b_normalized = b.replace('臺', '台')
        return SequenceMatcher(None, a_normalized, b_normalized).ratio()

    def _contains_match(self, query: str, target: str) -> Tuple[bool, float]:
        """
        檢查 query 是否包含 target 或相似
        返回: (是否匹配, 匹配分數)
        """
        query_n = query.replace('臺', '台')
        target_n = target.replace('臺', '台')
        
        # 精確包含
        if target_n in query_n:
            return True, 1.0
        
        # 去掉後綴再比較
        target_base = target_n
        for suffix in self.TOWNSHIP_SUFFIXES + self.VILLAGE_SUFFIXES + ['市', '縣']:
            if target_base.endswith(suffix):
                target_base = target_base[:-1]
                break
        
        if target_base and target_base in query_n:
            return True, 0.9
        
        # 模糊匹配
        sim = self._similarity(query_n, target_n)
        if sim >= 0.7:
            return True, sim
        
        return False, 0.0

    def _find_best_match(
        self, 
        query: str
    ) -> Tuple[Optional[County], Optional[Township], Optional[Village], Optional['Landmark'], float]:
        """
        智慧搜尋最佳匹配
        返回: (County, Township, Village, Landmark, confidence)
        """
        index = self._build_search_index()
        query_n = self._normalize_query(query)
        
        if not query_n:
            return None, None, None, None, 0.0
        
        best_county = None
        best_township = None
        best_village = None
        best_landmark = None
        best_score = 0.0
        
        # 策略0: 優先搜尋地標/景點 (最高優先)
        for lm_data in index['landmarks']:
            for search_name in lm_data['search_names']:
                matched, score = self._contains_match(query_n, search_name)
                if matched and score > best_score:
                    landmark = lm_data['obj']
                    best_landmark = landmark
                    best_county = landmark.county
                    best_township = landmark.township
                    best_village = None
                    best_score = score
        
        if best_score >= 0.9:
            return best_county, best_township, best_village, best_landmark, best_score
        
        # 策略1: 嘗試從村里開始匹配 (最精確)
        for v_data in index['villages']:
            for search_name in v_data['search_names']:
                matched, score = self._contains_match(query_n, search_name)
                if matched and score > best_score:
                    village = v_data['obj']
                    best_village = village
                    best_township = village.township
                    best_county = village.township.county
                    best_landmark = None
                    best_score = score
        
        if best_score >= 0.9:
            return best_county, best_township, best_village, best_landmark, best_score
        
        # 策略2: 嘗試鄉鎮區匹配
        for t_data in index['townships']:
            for search_name in t_data['search_names']:
                matched, score = self._contains_match(query_n, search_name)
                if matched and score > best_score:
                    township = t_data['obj']
                    best_township = township
                    best_county = township.county
                    best_village = None
                    best_score = score
        
        if best_score >= 0.8:
            return best_county, best_township, best_village, best_landmark, best_score
        
        # 策略3: 縣市別名匹配
        for alias, standard_name in self.COUNTY_ALIASES.items():
            if alias in query_n or alias.replace('臺', '台') in query_n:
                for c_data in index['counties']:
                    if c_data['obj'].name == standard_name:
                        # 找到縣市後，嘗試匹配剩餘的鄉鎮區
                        remaining = query_n.replace(alias, '').replace(alias.replace('臺', '台'), '')
                        if remaining:
                            for t_data in index['townships']:
                                if t_data['obj'].county_id == c_data['obj'].id:
                                    matched, score = self._contains_match(remaining, t_data['name'])
                                    if matched and score > best_score:
                                        best_county = c_data['obj']
                                        best_township = t_data['obj']
                                        best_village = None
                                        best_score = (1.0 + score) / 2
                        
                        if best_score == 0.0:
                            best_county = c_data['obj']
                            best_score = 0.7
                        break
        
        # 策略4: 純模糊搜尋 (最後手段)
        if best_score < 0.5:
            # 搜尋所有鄉鎮區名稱
            all_township_names = [t['name'] for t in index['townships']]
            close_matches = get_close_matches(query_n, all_township_names, n=3, cutoff=0.5)
            
            if close_matches:
                for t_data in index['townships']:
                    if t_data['name'] == close_matches[0]:
                        best_township = t_data['obj']
                        best_county = best_township.county
                        best_score = self._similarity(query_n, close_matches[0])
                        break
        
        return best_county, best_township, best_village, best_landmark, best_score

    def geocode(self, query: str, save_history: bool = True) -> GeoResult:
        """
        主要的地理編碼方法
        
        Args:
            query: 地名或地址字串 (支援模糊輸入，包含圖幅編號)
            save_history: 是否儲存查詢紀錄
            
        Returns:
            GeoResult 物件
        """
        if not query or not query.strip():
            return GeoResult(
                success=False,
                message="查詢字串不可為空"
            )
        
        # 檢查是否為圖幅編號格式 (4-8位數字或含有羅馬數字/方位)
        query_clean = query.strip().upper().replace('-', '').replace(' ', '')
        is_tile_code = (
            re.match(r'^\d{4,8}$', query_clean) or
            re.match(r'^\d{4}(I{1,3}|IV|[1-4])(NE|NW|SE|SW)?$', query_clean)
        )
        
        if is_tile_code:
            from .tile_converter import get_tile_converter
            converter = get_tile_converter()
            tile_result = converter.parse_tile_code(query)
            if tile_result.success:
                result = GeoResult(
                    latitude=tile_result.center_lat,
                    longitude=tile_result.center_lng,
                    full_address=f"圖幅 {tile_result.tile_code} ({tile_result.scale})",
                    confidence=1.0,
                    success=True,
                    message=f"圖幅編號解析成功 (比例尺: {tile_result.scale})"
                )
                # 儲存查詢紀錄
                if save_history:
                    GeoQuery.objects.create(
                        query_text=query,
                        latitude=tile_result.center_lat,
                        longitude=tile_result.center_lng,
                        confidence=1.0
                    )
                return result
        
        county, township, village, landmark, confidence = self._find_best_match(query)
        
        # 決定座標 (地標優先，床精確越優先)
        lat, lng = None, None
        if landmark:
            lat, lng = landmark.latitude, landmark.longitude
        elif village:
            lat, lng = village.latitude, village.longitude
        elif township:
            lat, lng = township.latitude, township.longitude
        elif county:
            lat, lng = county.latitude, county.longitude
        
        # 組合完整地址
        full_address_parts = []
        if landmark:
            # 地標直接顯示名稱
            full_address_parts.append(landmark.name)
        else:
            if county:
                full_address_parts.append(county.name)
            if township:
                full_address_parts.append(township.name)
            if village:
                full_address_parts.append(village.name)
        
        result = GeoResult(
            latitude=lat,
            longitude=lng,
            county=county.name if county else None,
            township=township.name if township else None,
            village=village.name if village else None,
            full_address=''.join(full_address_parts) if not landmark else landmark.name,
            confidence=round(confidence, 3),
            success=lat is not None,
            message="查詢成功" if lat else "無法匹配任何地點"
        )
        
        # 儲存查詢紀錄
        if save_history:
            GeoQuery.objects.create(
                query_text=query,
                matched_county=county,
                matched_township=township,
                matched_village=village,
                latitude=lat,
                longitude=lng,
                confidence=result.confidence
            )
        
        return result

    def search_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜尋建議 (用於自動完成)
        
        Args:
            query: 部分輸入的地名
            limit: 最多返回幾筆建議
            
        Returns:
            建議列表
        """
        if not query or len(query) < 1:
            return []
        
        index = self._build_search_index()
        query_n = query.replace('臺', '台')
        suggestions = []
        
        # 搜尋縣市
        for c_data in index['counties']:
            for name in c_data['search_names']:
                if query_n in name.replace('臺', '台'):
                    suggestions.append({
                        'type': 'county',
                        'name': c_data['obj'].name,
                        'full_name': c_data['obj'].name,
                        'latitude': c_data['obj'].latitude,
                        'longitude': c_data['obj'].longitude
                    })
                    break
        
        # 搜尋鄉鎮區
        for t_data in index['townships']:
            for name in t_data['search_names']:
                if query_n in name.replace('臺', '台'):
                    suggestions.append({
                        'type': 'township',
                        'name': t_data['obj'].name,
                        'full_name': t_data['full_name'],
                        'latitude': t_data['obj'].latitude,
                        'longitude': t_data['obj'].longitude
                    })
                    break
        
        # 搜尋村里
        for v_data in index['villages']:
            for name in v_data['search_names']:
                if query_n in name.replace('臺', '台'):
                    suggestions.append({
                        'type': 'village',
                        'name': v_data['obj'].name,
                        'full_name': v_data['full_name'],
                        'latitude': v_data['obj'].latitude,
                        'longitude': v_data['obj'].longitude
                    })
                    break
        
        return suggestions[:limit]


# 單例模式
_geocoding_service = None

def get_geocoding_service() -> GeocodingService:
    """取得 GeocodingService 單例"""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service
