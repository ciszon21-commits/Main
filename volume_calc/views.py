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
                df = pd.read_excel(file_path, sheet_name=sheet)
                # 清理數據：將 NaN 轉換為 None 並轉換為 list
                clean_df = df.where(pd.notnull(df), None)
                sheets_data[sheet] = {
                    'columns': clean_df.columns.tolist(),
                    'rows': clean_df.values.tolist()
                }
            context['excel_sheets'] = sheets_data
            context['sheet_names'] = xl.sheet_names
        except Exception as e:
            context['error'] = str(e)
            
        return context
