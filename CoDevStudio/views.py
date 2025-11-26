from django.shortcuts import render


def home(request):
    """
    CoDev Studio 首頁視圖
    顯示歡迎頁面，介紹平台特色與開發流程
    """
    return render(request, 'home.html')
