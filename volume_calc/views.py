from django.views.generic import TemplateView

class CalculatorView(TemplateView):
    template_name = 'volume_calc/calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We can pass initial default parameters based on the Excel logic if needed
        context['default_base_area'] = 1029
        context['default_original_volume'] = 2000
        context['default_zone_type'] = '第三種住宅區'
        context['default_volume_ratio'] = 2.25
        return context
