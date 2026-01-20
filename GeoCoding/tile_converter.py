"""
台灣圖幅編號轉換工具
支援將台灣地形圖（1:5000, 1:25000, 1:50000, 1:100000）的圖幅編號轉換為經緯度座標

圖幅編號規則：
- 1:100,000 圖幅：使用四碼數字 (例如: 9523)
  - 前兩碼為經度方向編號，後兩碼為緯度方向編號
  - 起點為西南角，往東北方向遞增
  
- 1:50,000 圖幅：在 1:100,000 編號後加羅馬數字 I-IV (例如: 9523-III)
  - 將 1:100,000 圖幅分為 4 格 (2x2)
  
- 1:25,000 圖幅：在 1:50,000 編號後加方位 NE/SE/SW/NW (例如: 9523-III-SW)
  - 將 1:50,000 圖幅再分為 4 格 (2x2)

- 1:5,000 圖幅：使用更細的網格劃分
  
TWD97 座標系統參數：
- 中央經線：121度 (台灣本島)、119度 (金門馬祖澎湖)
- 橢球體：GRS-80
- 投影方式：橫麥卡托 (Transverse Mercator)
"""
import re
import math
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class TileCodeResult:
    """圖幅編號解析結果"""
    tile_code: str
    scale: str  # '1:5000', '1:25000', '1:50000', '1:100000'
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    sw_lat: Optional[float] = None  # 西南角緯度
    sw_lng: Optional[float] = None  # 西南角經度
    ne_lat: Optional[float] = None  # 東北角緯度
    ne_lng: Optional[float] = None  # 東北角經度
    success: bool = False
    message: str = ""


class TileCodeConverter:
    """
    台灣圖幅編號轉換器
    
    支援格式：
    - 4位數代碼 (1:100,000): 9523
    - 6位數代碼 + 羅馬數字 (1:50,000): 9523-III 或 9523III
    - 完整代碼 (1:25,000): 9523-III-SW 或 9523IIISW
    - 5位數代碼 (1:5,000 NLSC格式): 例如 95234001
    """
    
    # 台灣本島 1:100,000 圖幅的基準參數
    # 基準點 (西南角) 約為北緯 21度、東經 119度
    BASE_LAT = 21.0  # 起始緯度
    BASE_LNG = 119.0  # 起始經度
    
    # 1:100,000 圖幅尺寸 (度)
    TILE_100K_LAT = 0.5  # 30分 = 0.5度
    TILE_100K_LNG = 0.5  # 30分 = 0.5度
    
    # 羅馬數字對應
    ROMAN_TO_OFFSET = {
        'I': (0.5, 0.5),    # 東北 (右上)
        'II': (0.0, 0.5),   # 西北 (左上)
        'III': (0.0, 0.0),  # 西南 (左下)
        'IV': (0.5, 0.0),   # 東南 (右下)
        '1': (0.5, 0.5),
        '2': (0.0, 0.5),
        '3': (0.0, 0.0),
        '4': (0.5, 0.0),
    }
    
    # 方位對應
    QUADRANT_TO_OFFSET = {
        'NE': (0.5, 0.5),   # 東北 (右上)
        'NW': (0.0, 0.5),   # 西北 (左上)
        'SW': (0.0, 0.0),   # 西南 (左下)
        'SE': (0.5, 0.0),   # 東南 (右下)
    }
    
    def parse_tile_code(self, code: str) -> TileCodeResult:
        """
        解析圖幅編號並轉換為座標
        
        Args:
            code: 圖幅編號字串
            
        Returns:
            TileCodeResult 物件
        """
        if not code:
            return TileCodeResult(
                tile_code=code,
                scale='unknown',
                success=False,
                message="圖幅編號不可為空"
            )
        
        # 標準化輸入：移除空白和橫線，轉大寫
        code_clean = code.strip().upper().replace('-', '').replace(' ', '')
        
        # 嘗試匹配 1:5000 NLSC 8位數格式 (例如: 95231234)
        match_5k = re.match(r'^(\d{4})(\d{4})$', code_clean)
        if match_5k:
            return self._parse_5k_tile(code, match_5k.group(1), match_5k.group(2))
        
        # 嘗試匹配 1:25,000 格式 (例如: 9523IIISW)
        match_25k = re.match(r'^(\d{4})(I{1,3}|IV|[1-4])(NE|NW|SE|SW)$', code_clean)
        if match_25k:
            return self._parse_25k_tile(code, match_25k.group(1), 
                                        match_25k.group(2), match_25k.group(3))
        
        # 嘗試匹配 1:50,000 格式 (例如: 9523III)
        match_50k = re.match(r'^(\d{4})(I{1,3}|IV|[1-4])$', code_clean)
        if match_50k:
            return self._parse_50k_tile(code, match_50k.group(1), match_50k.group(2))
        
        # 嘗試匹配 1:100,000 格式 (例如: 9523)
        match_100k = re.match(r'^(\d{4})$', code_clean)
        if match_100k:
            return self._parse_100k_tile(code, match_100k.group(1))
        
        return TileCodeResult(
            tile_code=code,
            scale='unknown',
            success=False,
            message=f"無法識別的圖幅編號格式: {code}"
        )
    
    def _parse_100k_tile(self, original_code: str, base_code: str) -> TileCodeResult:
        """解析 1:100,000 圖幅"""
        try:
            col = int(base_code[:2])  # 經度方向 (東西)
            row = int(base_code[2:])  # 緯度方向 (南北)
            
            # 計算西南角座標
            sw_lng = self.BASE_LNG + (col - 95) * self.TILE_100K_LNG
            sw_lat = self.BASE_LAT + (row - 20) * self.TILE_100K_LAT
            
            # 計算東北角座標
            ne_lng = sw_lng + self.TILE_100K_LNG
            ne_lat = sw_lat + self.TILE_100K_LAT
            
            # 計算中心點
            center_lng = (sw_lng + ne_lng) / 2
            center_lat = (sw_lat + ne_lat) / 2
            
            return TileCodeResult(
                tile_code=original_code,
                scale='1:100000',
                center_lat=center_lat,
                center_lng=center_lng,
                sw_lat=sw_lat,
                sw_lng=sw_lng,
                ne_lat=ne_lat,
                ne_lng=ne_lng,
                success=True,
                message="解析成功"
            )
        except Exception as e:
            return TileCodeResult(
                tile_code=original_code,
                scale='1:100000',
                success=False,
                message=f"解析錯誤: {str(e)}"
            )
    
    def _parse_50k_tile(self, original_code: str, base_code: str, roman: str) -> TileCodeResult:
        """解析 1:50,000 圖幅"""
        # 先解析 1:100,000 基礎
        result_100k = self._parse_100k_tile(original_code, base_code)
        if not result_100k.success:
            return result_100k
        
        # 取得象限偏移
        offset = self.ROMAN_TO_OFFSET.get(roman)
        if not offset:
            return TileCodeResult(
                tile_code=original_code,
                scale='1:50000',
                success=False,
                message=f"無效的象限代碼: {roman}"
            )
        
        # 1:50,000 尺寸為 1:100,000 的一半
        tile_lng = self.TILE_100K_LNG / 2
        tile_lat = self.TILE_100K_LAT / 2
        
        # 計算新的西南角
        sw_lng = result_100k.sw_lng + offset[0] * self.TILE_100K_LNG
        sw_lat = result_100k.sw_lat + offset[1] * self.TILE_100K_LAT
        
        # 注意：由於 ROMAN_TO_OFFSET 使用相對比例，需要調整
        sw_lng = result_100k.sw_lng + (1 if offset[0] > 0 else 0) * tile_lng
        sw_lat = result_100k.sw_lat + (1 if offset[1] > 0 else 0) * tile_lat
        
        ne_lng = sw_lng + tile_lng
        ne_lat = sw_lat + tile_lat
        
        center_lng = (sw_lng + ne_lng) / 2
        center_lat = (sw_lat + ne_lat) / 2
        
        return TileCodeResult(
            tile_code=original_code,
            scale='1:50000',
            center_lat=center_lat,
            center_lng=center_lng,
            sw_lat=sw_lat,
            sw_lng=sw_lng,
            ne_lat=ne_lat,
            ne_lng=ne_lng,
            success=True,
            message="解析成功"
        )
    
    def _parse_25k_tile(self, original_code: str, base_code: str, 
                        roman: str, quadrant: str) -> TileCodeResult:
        """解析 1:25,000 圖幅"""
        # 先解析 1:50,000 基礎
        result_50k = self._parse_50k_tile(original_code, base_code, roman)
        if not result_50k.success:
            return result_50k
        
        # 取得方位偏移
        offset = self.QUADRANT_TO_OFFSET.get(quadrant)
        if not offset:
            return TileCodeResult(
                tile_code=original_code,
                scale='1:25000',
                success=False,
                message=f"無效的方位代碼: {quadrant}"
            )
        
        # 1:25,000 尺寸為 1:50,000 的一半
        tile_lng = self.TILE_100K_LNG / 4
        tile_lat = self.TILE_100K_LAT / 4
        
        parent_width = self.TILE_100K_LNG / 2
        parent_height = self.TILE_100K_LAT / 2
        
        sw_lng = result_50k.sw_lng + (1 if offset[0] > 0 else 0) * tile_lng
        sw_lat = result_50k.sw_lat + (1 if offset[1] > 0 else 0) * tile_lat
        
        ne_lng = sw_lng + tile_lng
        ne_lat = sw_lat + tile_lat
        
        center_lng = (sw_lng + ne_lng) / 2
        center_lat = (sw_lat + ne_lat) / 2
        
        return TileCodeResult(
            tile_code=original_code,
            scale='1:25000',
            center_lat=center_lat,
            center_lng=center_lng,
            sw_lat=sw_lat,
            sw_lng=sw_lng,
            ne_lat=ne_lat,
            ne_lng=ne_lng,
            success=True,
            message="解析成功"
        )
    
    def _parse_5k_tile(self, original_code: str, base_code: str, 
                       sub_code: str) -> TileCodeResult:
        """
        解析 1:5,000 圖幅 (NLSC 8位數格式)
        
        1:5,000 圖幅約覆蓋 1.875' x 1.25' (經 x 緯)
        = 0.03125° x 0.02083°
        """
        # 先解析基礎的 1:100,000
        result_100k = self._parse_100k_tile(original_code, base_code)
        if not result_100k.success:
            return result_100k
        
        try:
            sub_num = int(sub_code)
            # 計算在 1:100,000 圖幅內的相對位置
            # 假設 1:100,000 被分為 16x24 = 384 個 1:5,000 圖幅
            col_5k = (sub_num % 100) - 1  # 0-15
            row_5k = (sub_num // 100) - 1  # 0-23
            
            tile_lng = self.TILE_100K_LNG / 16
            tile_lat = self.TILE_100K_LAT / 24
            
            sw_lng = result_100k.sw_lng + col_5k * tile_lng
            sw_lat = result_100k.sw_lat + row_5k * tile_lat
            
            ne_lng = sw_lng + tile_lng
            ne_lat = sw_lat + tile_lat
            
            center_lng = (sw_lng + ne_lng) / 2
            center_lat = (sw_lat + ne_lat) / 2
            
            return TileCodeResult(
                tile_code=original_code,
                scale='1:5000',
                center_lat=center_lat,
                center_lng=center_lng,
                sw_lat=sw_lat,
                sw_lng=sw_lng,
                ne_lat=ne_lat,
                ne_lng=ne_lng,
                success=True,
                message="解析成功"
            )
        except Exception as e:
            return TileCodeResult(
                tile_code=original_code,
                scale='1:5000',
                success=False,
                message=f"解析錯誤: {str(e)}"
            )
    
    def coordinate_to_tile(self, lat: float, lng: float, 
                          scale: str = '1:5000') -> Optional[str]:
        """
        根據經緯度座標計算對應的圖幅編號
        
        Args:
            lat: 緯度
            lng: 經度
            scale: 目標比例尺 ('1:100000', '1:50000', '1:25000', '1:5000')
            
        Returns:
            圖幅編號字串
        """
        # 計算 1:100,000 基礎編號
        col = int((lng - self.BASE_LNG) / self.TILE_100K_LNG) + 95
        row = int((lat - self.BASE_LAT) / self.TILE_100K_LAT) + 20
        
        base_code = f"{col:02d}{row:02d}"
        
        if scale == '1:100000':
            return base_code
        
        # 計算在 1:100,000 圖幅內的相對位置
        rel_lng = (lng - self.BASE_LNG) % self.TILE_100K_LNG
        rel_lat = (lat - self.BASE_LAT) % self.TILE_100K_LAT
        
        # 1:50,000 象限
        half_lng = self.TILE_100K_LNG / 2
        half_lat = self.TILE_100K_LAT / 2
        
        if rel_lng >= half_lng and rel_lat >= half_lat:
            roman = 'I'
        elif rel_lng < half_lng and rel_lat >= half_lat:
            roman = 'II'
        elif rel_lng < half_lng and rel_lat < half_lat:
            roman = 'III'
        else:
            roman = 'IV'
        
        if scale == '1:50000':
            return f"{base_code}-{roman}"
        
        # 1:25,000 方位
        quarter_lng = self.TILE_100K_LNG / 4
        quarter_lat = self.TILE_100K_LAT / 4
        
        sub_rel_lng = rel_lng % half_lng
        sub_rel_lat = rel_lat % half_lat
        
        if sub_rel_lng >= quarter_lng and sub_rel_lat >= quarter_lat:
            quadrant = 'NE'
        elif sub_rel_lng < quarter_lng and sub_rel_lat >= quarter_lat:
            quadrant = 'NW'
        elif sub_rel_lng < quarter_lng and sub_rel_lat < quarter_lat:
            quadrant = 'SW'
        else:
            quadrant = 'SE'
        
        if scale == '1:25000':
            return f"{base_code}-{roman}-{quadrant}"
        
        # 1:5,000
        tile_lng = self.TILE_100K_LNG / 16
        tile_lat = self.TILE_100K_LAT / 24
        
        col_5k = int(rel_lng / tile_lng) + 1
        row_5k = int(rel_lat / tile_lat) + 1
        
        sub_code = f"{row_5k:02d}{col_5k:02d}"
        return f"{base_code}{sub_code}"


# 單例模式
_tile_converter = None

def get_tile_converter() -> TileCodeConverter:
    """取得 TileCodeConverter 單例"""
    global _tile_converter
    if _tile_converter is None:
        _tile_converter = TileCodeConverter()
    return _tile_converter
