from django.views.generic import TemplateView
import pandas as pd
import os
from django.conf import settings

class CalcPageView(TemplateView):
    template_name = 'volume_calc/calc_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_path = os.path.join(settings.BASE_DIR, 'reference', '容積計算.xlsx')
        
        try:
            xl = pd.ExcelFile(file_path)
            sheets_data = {}
            for sheet in xl.sheet_names:
                # 重新讀取，不預設 header，以便我們手動處理
                df = pd.read_excel(file_path, sheet_name=sheet, header=None)
                
                # 移除完全為空的行與列
                df = df.dropna(how='all').dropna(axis=1, how='all')
                
                # 動態尋找真正的數據開始處或清理標題
                # 策略：如果前幾行有大量 NaN，則可能是合併單元格，我們嘗試合併它們
                rows = df.values.tolist()
                if not rows:
                    sheets_data[sheet] = {'columns': [], 'rows': []}
                    continue
                
                # 將 NaN 轉換為空字串以便顯示，且處理 None
                processed_rows = []
                for r in rows:
                    processed_rows.append([("" if pd.isna(c) else c) for c in r])
                
                # 這裡我們不移除 "Unnamed"，因為 header=None 時會是數字索引
                # 我們直接把第一行當作欄位，如果第一行看起來像資料則補一個空 header
                sheets_data[sheet] = {
                    'columns': [f"Col {i+1}" for i in range(len(processed_rows[0]))],
                    'rows': processed_rows
                }
            context['excel_sheets'] = sheets_data
            context['sheet_names'] = xl.sheet_names
        except Exception as e:
            context['error'] = str(e)
            
        return context
