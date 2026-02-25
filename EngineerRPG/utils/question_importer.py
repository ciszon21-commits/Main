"""
題目批次匯入工具 - 更新版本
配合 Question 模型的 JSONField 結構
"""

import csv
import io
from openpyxl import load_workbook
from django.db import transaction
from EngineerRPG.models import Question, SkillNode


class QuestionImporter:
    """題目匯入器"""
    
    def __init__(self):
        print("QuestionImporter initialized")
        self.errors = []
        self.success_count = 0
        self.skip_count = 0
    
    def import_from_file(self, file):
        """從檔案匯入題目"""
        if file.name.endswith('.csv'):
            return self._import_csv(file)
        elif file.name.endswith('.xlsx'):
            return self._import_excel(file)
        else:
            raise ValueError('不支援的檔案格式')
    
    def _import_csv(self, file):
        """匯入 CSV 檔案"""
        decoded_file = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded_file))
        return self._process_rows(reader)
    
    def _import_excel(self, file):
        """匯入 Excel 檔案"""
        wb = load_workbook(file)
        ws = wb.active
        
        # Robust header reading: strip whitespace and ignore None
        headers = [str(cell.value).strip() if cell.value else f"Column_{i}" for i, cell in enumerate(ws[1])]
        
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            # Extend headers or row if lengths don't match (though zip handles shortening)
            row_dict = dict(zip(headers, row))
            rows.append(row_dict)
        
        return self._process_rows(rows)
    
    @transaction.atomic
    def _process_rows(self, rows):
        """處理資料列"""
        print(f"Processing {len(rows) if isinstance(rows, list) else 'CSV iterator'} rows")
        for idx, row in enumerate(rows, start=2):
            try:
                # Normalize row keys (support aliases)
                row = self._normalize_row(row)
                
                # Debug info for first row or error
                if idx == 2:
                    print(f"Row {idx} keys: {list(row.keys())}")
                    print(f"Row {idx} content: {row}")
                
                self._upsert_question(row)
                self.success_count += 1
            except Exception as e:
                self.errors.append(f'第 {idx} 列: {str(e)}')
                self.skip_count += 1
        
        return {
            'success': self.success_count,
            'skip': self.skip_count,
            'errors': self.errors
        }

    def _normalize_row(self, row):
        """標準化欄位名稱 (支援別名)"""
        alias_map = {
            '內容': '題目內容',
            '類型': '題目類型',
            '詳解': '答案解析',
            '解析': '答案解析',
            '啟用狀態': '啟用',
            '答案': '正確答案',
        }
        
        new_row = {}
        for key, value in row.items():
            if not key: continue
            # Strip key whitespace
            key = str(key).strip()
            # Map alias if exists
            new_key = alias_map.get(key, key)
            new_row[new_key] = value
        return new_row
    
    def _upsert_question(self, row):
        """新增或更新題目"""
        required_fields = ['題目內容', '題目類型', '正確答案', '難度']
        
        # Check all required fields first and accumulate missing ones
        missing = []
        for field in required_fields:
            if not row.get(field):
                missing.append(field)
        
        if missing:
            # Include available keys in error message for debugging
            available_keys = list(row.keys())
            raise ValueError(f'缺少必填欄位: {", ".join(missing)}。 (讀取到的欄位: {available_keys})')
        
        # 處理選項 - 轉為 JSON
        options = {}
        for key, option_key in [('選項A', 'A'), ('選項B', 'B'), ('選項C', 'C'), ('選項D', 'D')]:
            if row.get(key):
                options[option_key] = str(row[key])
        
        # 處理答案 - 轉為 JSON
        answer_str = str(row['正確答案']).strip().upper()
        if ',' in answer_str or ';' in answer_str:
            # 多選
            separator = ',' if ',' in answer_str else ';'
            correct_answer = [a.strip() for a in answer_str.split(separator)]
        else:
            # 單選或是非
            correct_answer = answer_str
            
        # 準備欄位資料
        defaults = {
            'content': row['題目內容'],
            'question_type': self._get_question_type(row['題目類型']),
            'options': options,
            'correct_answer': correct_answer,
            'explanation': row.get('答案解析', ''),
            'difficulty': self._get_difficulty(row['難度']),
            'is_active': str(row.get('啟用', 'Y')).upper() == 'Y'
        }

        # 處理分類
        if row.get('分類'):
            from EngineerRPG.models import QuestionCategory
            category_name = str(row['分類']).strip()
            try:
                category = QuestionCategory.objects.get(name=category_name)
                defaults['category'] = category
            except QuestionCategory.DoesNotExist:
                pass  # 分類不存在則保留無分類 (或使用預設)
        
        # 檢查是否有 ID 進行更新
        question_id = row.get('ID')
        if question_id:
            try:
                question = Question.objects.get(id=question_id)
                for key, value in defaults.items():
                    setattr(question, key, value)
                question.save()
                return question
            except Question.DoesNotExist:
                # ID 不存在，視為新題目（忽略 ID，讓 DB 自動產生新 ID）
                pass

        # 建立新題目
        question = Question(**defaults)
        question.save()
        
        return question
    
    def _get_question_type(self, type_str):
        """取得題目類型代碼"""
        type_mapping = {
            '單選': 'SINGLE',
            '多選': 'MULTIPLE',
            '是非': 'TRUEFALSE',
        }
        return type_mapping.get(type_str, 'SINGLE')
    
    def _get_difficulty(self, difficulty_str):
        """取得難度代碼"""
        difficulty_mapping = {
            'S': 'S', 'S級': 'S',
            'A': 'A', 'A級': 'A',
            'B': 'B', 'B級': 'B', '中等': 'B',
            'C': 'C', 'C級': 'C', '簡單': 'C',
        }
        return difficulty_mapping.get(difficulty_str, 'B')


def generate_template_csv():
    """產生匯入範本 CSV"""
    template = """ID,題目內容,題目類型,選項A,選項B,選項C,選項D,正確答案,答案解析,難度,分類,啟用
,工地主任應具備哪些資格？,單選,土木技師,建築師,營造業專任工程人員,以上皆可,D,工地主任需具備相關專業資格,B,工務行政,Y
,下列何者為施工安全重點？,多選,佩戴安全帽,設置安全網,定期檢查,僅A,"A,B,C",施工安全需要多重防護措施,C,職安衛,Y
,混凝土澆置前需進行鋼筋檢查,是非,,,,,TRUE,確保結構安全的必要步驟,C,施工管理,Y"""
    
    return template


def generate_template_excel():
    """產生匯入範本 Excel"""
    from openpyxl import Workbook
    from io import BytesIO
    
    wb = Workbook()
    ws = wb.active
    ws.title = "題目匯入範本"
    
    headers = [
        'ID', '題目內容', '題目類型', '選項A', '選項B', '選項C', '選項D',
        '正確答案', '答案解析', '難度', '分類', '啟用'
    ]
    ws.append(headers)
    
    examples = [
        [
            '', '工地主任應具備哪些資格？', '單選', '土木技師', '建築師', 
            '營造業專任工程人員', '以上皆可', 'D', '工地主任需具備相關專業資格',
            'B', '工務行政', 'Y'
        ],
        [
            '', '下列何者為施工安全重點？', '多選', '佩戴安全帽', '設置安全網',
            '定期檢查', '僅A', 'A,B,C', '施工安全需要多重防護措施',
            'C', '職安衛', 'Y'
        ],
        [
            '', '混凝土澆置前需進行鋼筋檢查', '是非', '', '',
            '', '', 'TRUE', '確保結構安全的必要步驟',
            'C', '施工管理', 'Y'
        ],
    ]
    
    for example in examples:
        ws.append(example)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output
