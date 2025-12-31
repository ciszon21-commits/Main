from django.core.management.base import BaseCommand
from openpyxl import load_workbook
import re
from CarbonEstimation.models import MainCategory, ComponentItem
from decimal import Decimal, InvalidOperation


class Command(BaseCommand):
    help = '從 Excel 檔案匯入碳排資料'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='ref/常用組件碳排概算表單.xlsx',
            help='Excel 檔案路徑'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        self.stdout.write(f"正在讀取檔案: {file_path}")
        
        # 載入 Excel
        wb = load_workbook(file_path)
        ws = wb.active
        
        # 清除舊資料
        self.stdout.write("清除舊資料...")
        ComponentItem.objects.all().delete()
        MainCategory.objects.all().delete()
        
        # 儲存分類和項目
        categories_dict = {}  # {code: MainCategory object}
        items_to_create = []
        
        # 第一次掃描：找出所有主要分類
        self.stdout.write("第一次掃描：識別主要分類...")
        for row_idx in range(1, ws.max_row + 1):
            col_a = ws.cell(row_idx, 1).value
            col_b = ws.cell(row_idx, 2).value
            
            if col_a and col_b:
                col_a_str = str(col_a).strip()
                col_b_str = str(col_b).strip()
                
                # 主要分類：如 "一.", "二.", "三." 等（不含子項目）
                # 使用更精確的判斷：只有一個中文數字+句點
                if self._is_main_category(col_a_str):
                    if col_a_str not in categories_dict:
                        order = len(categories_dict) + 1
                        category = MainCategory.objects.create(
                            code=col_a_str,
                            name=col_b_str,
                            order=order
                        )
                        categories_dict[col_a_str] = category
                        self.stdout.write(f"  創建分類 {order}: {col_a_str} {col_b_str}")
        
        self.stdout.write(f"共創建 {len(categories_dict)} 個主要分類")
        
        # 第二次掃描：匯入所有項目
        self.stdout.write("\n第二次掃描：匯入組件項目...")
        current_category = None
        item_count = 0
        
        for row_idx in range(1, ws.max_row + 1):
            col_a = ws.cell(row_idx, 1).value  # 項次
            col_b = ws.cell(row_idx, 2).value  # 工作項目
            
            if not col_a or not col_b:
                continue
                
            col_a_str = str(col_a).strip()
            col_b_str = str(col_b).strip()
            
            # 跳過標題行和主要分類行
            if col_a_str in ['項次', '一'] or self._is_main_category(col_a_str):
                # 更新當前分類
                if col_a_str in categories_dict:
                    current_category = categories_dict[col_a_str]
                continue
            
            # 判斷是否為有效項目（格式如 "一.1.1", "二.3", etc.）
            if not self._is_valid_item(col_a_str):
                continue
            
            # 確定該項目所屬的分類
            item_category = self._find_category_for_item(col_a_str, categories_dict)
            if not item_category:
                item_category = current_category
            
            if not item_category:
                self.stdout.write(self.style.WARNING(f"  Row {row_idx}: 無法確定分類 - {col_a_str}"))
                continue
            
            # 讀取其他欄位
            unit = self._get_cell_value(ws, row_idx, 3)  # C: 單位
            description = self._get_cell_value(ws, row_idx, 4)  # D: 說明
            default_qty = self._get_decimal_value(ws, row_idx, 5)  # E: 數量
            carbon_before = self._get_decimal_value(ws, row_idx, 6)  # F
            carbon_after = self._get_decimal_value(ws, row_idx, 7)  # G
            cost_before = self._get_decimal_value(ws, row_idx, 8)  # H
            cost_after = self._get_decimal_value(ws, row_idx, 9)  # I
            carbon_unit = self._get_cell_value(ws, row_idx, 14)  # N
            notes = self._get_cell_value(ws, row_idx, 15)  # O
            reference = self._get_cell_value(ws, row_idx, 16)  # P
            
            # 確定階層
            item_level = self._detect_level(col_a_str)
            
            # 創建項目
            try:
                item = ComponentItem.objects.create(
                    category=item_category,
                    item_no=col_a_str,
                    level=item_level,
                    work_item=col_b_str,
                    unit=unit or '',
                    description=description or '',
                    default_quantity=default_qty,
                    carbon_before=carbon_before,
                    carbon_after=carbon_after,
                    cost_before=cost_before,
                    cost_after=cost_after,
                    carbon_unit=carbon_unit or '',
                    notes=notes or '',
                    reference=reference or '',
                    order=item_count
                )
                item_count += 1
                
                if item_count % 10 == 0:
                    self.stdout.write(f"  已匯入 {item_count} 個項目...")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"  Row {row_idx} 匯入失敗: {col_a_str} - {str(e)}"
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n匯入完成！共 {len(categories_dict)} 個分類，{item_count} 個項目"
        ))
    
    def _is_main_category(self, code):
        """判斷是否為主要分類（如 '一', '二', '十四'）"""
        # 主要分類為純中文數字，沒有句點或其他字符
        chinese_numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四']
        return code in chinese_numbers
    
    def _is_valid_item(self, code):
        """判斷是否為有效項目編號"""
        # 格式: 一.1, 一.1.1, 二.3.2 等
        pattern = r'^[一二三四五六七八九十]+\.\d+(\.\d+)?(\.\d+)?$'
        return bool(re.match(pattern, code))
    
    def _find_category_for_item(self, item_no, categories_dict):
        """根據項目編號找出所屬分類"""
        # 提取開頭的中文數字部分（不包含句點）
        match = re.match(r'^([一二三四五六七八九十]+)\.', item_no)
        if match:
            category_code = match.group(1)  # 不加句點
            return categories_dict.get(category_code)
        return None
    
    def _detect_level(self, item_no):
        """偵測項目階層
        1: 第一階 - 如 '一', '二', '三'
        2: 第二階 - 如 '一.1', '二.2', '三.5'
        3: 第三階 - 如 '一.1.1', '二.3.4', '三.2.1'
        """
        # 去除開頭結尾空白
        item_no = item_no.strip()
        
        # 計算句點數量
        dot_count = item_no.count('.')
        
        if dot_count == 0:
            # 沒有句點 = 第一階 (但通常不會有這種情況，因為MainCategory已經被過濾掉)
            return 1
        elif dot_count == 1:
            # 一個句點 = 第二階 (如 '一.1')
            return 2
        else:
            # 兩個或以上句點 = 第三階 (如 '一.1.1' 或 '五.4.1.1')
            return 3
    
    def _get_cell_value(self, ws, row, col):
        """取得儲存格值（字串）"""
        value = ws.cell(row, col).value
        if value is None:
            return ''
        # 排除公式
        if isinstance(value, str) and value.startswith('='):
            return ''
        return str(value).strip()
    
    def _get_decimal_value(self, ws, row, col):
        """取得儲存格值（數值）"""
        value = ws.cell(row, col).value
        if value is None:
            return None
        # 排除公式
        if isinstance(value, str) and value.startswith('='):
            return None
        
        try:
            # 處理字串數字（可能包含千分位逗號）
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
