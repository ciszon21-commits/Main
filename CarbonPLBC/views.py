"""視圖函數"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import GlobalSettings
from .forms import CarbonEmissionInputForm, GlobalSettingsForm
from .services import CarbonEmissionCalculator


def index_view(request):
    """主頁：單頁表單與計算結果"""
    settings = GlobalSettings.load()
    result = None
    
    if request.method == 'POST':
        form = CarbonEmissionInputForm(request.POST)
        if form.is_valid():
            # 儲存輸入數據
            input_data = form.save()
            
            # 執行計算
            calculator = CarbonEmissionCalculator(input_data)
            result = calculator.calculate_all()
            
            messages.success(request, '計算完成！')
    else:
        form = CarbonEmissionInputForm()
    
    context = {
        'form': form,
        'settings': settings,
        'result': result,
    }
    
    return render(request, 'CarbonPLBC/index.html', context)


@staff_member_required
def settings_view(request):
    """全域設定管理（僅管理員可訪問）"""
    settings = GlobalSettings.load()
    
    if request.method == 'POST':
        form = GlobalSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, '設定已更新！')
            return redirect('carbonplbc:settings')
    else:
        form = GlobalSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
    }
    
    return render(request, 'CarbonPLBC/settings.html', context)
