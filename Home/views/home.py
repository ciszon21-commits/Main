from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic import View




class HomeView(View):
    """
    CoDev Studio 首頁視圖
    顯示歡迎頁面，介紹平台特色與開發流程
    """
    template_name = 'Home/home.html'
    def get(self, request:'HttpRequest', **kwargs):
        return render(request, self.template_name, kwargs)

