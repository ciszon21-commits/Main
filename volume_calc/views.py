from numbers import Real
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.views.generic import TemplateView


def _format_cell(value):
    if pd.isna(value):
        return ''
    if isinstance(value, Real) and float(value).is_integer():
        return str(int(value))
    if isinstance(value, Real):
        return f'{float(value):.2f}'
    return str(value)


def _load_building_mass_sheet(excel_path: Path, sheet_index: int, title: str):
    df = pd.read_excel(excel_path, sheet_name=sheet_index, header=None)
    # Keep only used range so we do not render a huge blank grid.
    df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)

    rows = [[_format_cell(cell) for cell in row] for row in df.values.tolist()]
    headers = [f'欄位 {i + 1}' for i in range(df.shape[1])]

    return {
        'title': title,
        'headers': headers,
        'rows': rows,
    }


class CalculatorView(TemplateView):
    template_name = 'volume_calc/calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['default_base_area'] = 1029
        context['default_original_volume'] = 2000
        context['default_zone_type'] = '蝚砌?蝔桐?摰?'
        context['default_volume_ratio'] = 2.25

        context['building_mass_sheets'] = []
        context['building_mass_error'] = ''

        try:
            reference_dir = Path(settings.BASE_DIR) / 'reference'
            excel_files = sorted(reference_dir.glob('*.xlsx'))
            if not excel_files:
                raise FileNotFoundError('No Excel file found in reference folder.')

            excel_path = excel_files[0]
            context['building_mass_sheets'] = [
                _load_building_mass_sheet(excel_path, 2, '北市建築量體'),
                _load_building_mass_sheet(excel_path, 3, '新北建築量體'),
            ]
        except Exception as exc:
            context['building_mass_error'] = f'讀取建築量體工作表失敗：{exc}'

        return context
