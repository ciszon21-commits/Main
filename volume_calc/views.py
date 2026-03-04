from django.views.generic import TemplateView

class CalcPageView(TemplateView):
    template_name = 'volume_calc/calc_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 這裡未來可以加入預設資料或從 Excel 解析出的初始化獎勵項目
        return context
