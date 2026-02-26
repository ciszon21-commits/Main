import io
import pandas as pd
from datetime import datetime
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .services import GoogleNewsService, NewsAnalyzer
from .models import SearchRecord

def index(request):
    """
    搜尋首頁與結果呈現
    """
    if request.method == "POST":
        keywords = request.POST.get('keywords', '').strip()
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        topic_words = request.POST.get('topic_words', '')
        stop_words = request.POST.get('stop_words', '')
        wc_color = request.POST.get('wc_color', 'viridis')
        action = request.POST.get('action', 'search')
        
        if action == 'search':
            if not keywords:
                return render(request, 'NewsInsight/search.html', {'error': '請輸入關鍵字'})

            # 儲存查詢紀錄
            user = request.user if request.user.is_authenticated else None
            SearchRecord.objects.create(
                user=user,
                keywords=keywords,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                topic_words=topic_words,
                stop_words=stop_words
            )
            
            # 搜尋新聞
            articles = GoogleNewsService.search_news(keywords, start_date, end_date)
            
            # 依發布日期排序 (新到舊)
            if articles:
                articles.sort(key=lambda x: x['pub_date'], reverse=True)
                
            # 存取在 session 中供匯出 Excel 及重新分析使用
            request.session['cached_articles'] = [
                {
                    'title': a['title'],
                    'link': a['link'],
                    'source': a['source'],
                    'pub_date': a['pub_date'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(a['pub_date'], datetime) else str(a['pub_date']),
                    'summary': a['summary']
                } for a in articles
            ]
            request.session['last_keywords'] = keywords
            request.session['last_start_date'] = start_date
            request.session['last_end_date'] = end_date
            
        elif action == 'reanalyze':
            # 從 session 讀取快取文章
            articles = request.session.get('cached_articles', [])
            keywords = request.session.get('last_keywords', keywords)
            start_date = request.session.get('last_start_date', start_date)
            end_date = request.session.get('last_end_date', end_date)
            
            # 確保 pub_date 是 datetime 以利排序與圖表產生
            for a in articles:
                if isinstance(a['pub_date'], str):
                    try:
                        a['pub_date'] = datetime.strptime(a['pub_date'], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
        
        # 準備分析
        texts = [a['title'] for a in articles] if articles else []
        
        wordcloud_img = None
        freq_chart_data = None
        timeline_chart_data = None
        
        if texts:
            wordcloud_img = NewsAnalyzer.generate_wordcloud_base64(texts, topic_words, stop_words, colormap=wc_color)
            freq_data_dict = NewsAnalyzer.generate_frequency_data(texts, topic_words, stop_words)
            if freq_data_dict:
                freq_chart_data = json.dumps(freq_data_dict)
            
            timeline_data_dict = NewsAnalyzer.generate_timeline_data(articles)
            if timeline_data_dict:
                timeline_chart_data = json.dumps(timeline_data_dict)
            
        context = {
            'keywords': keywords,
            'start_date': start_date,
            'end_date': end_date,
            'topic_words': topic_words,
            'stop_words': stop_words,
            'wc_color': wc_color,
            'articles': articles,
            'wordcloud_img': wordcloud_img,
            'freq_chart_data': freq_chart_data,
            'timeline_chart_data': timeline_chart_data,
        }
        return render(request, 'NewsInsight/results.html', context)
        
    return render(request, 'NewsInsight/search.html')

def export_excel(request):
    """
    匯出新聞結果至 Excel
    """
    articles = request.session.get('cached_articles', [])
    if not articles:
        return HttpResponse("沒有可匯出的資料", status=400)
        
    df = pd.DataFrame(articles)
    df.columns = ['新聞標題', '連結', '媒體來源', '發布時間', '內容摘要']
    
    # 將資料寫入記憶體
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='輿情分析')
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"NewsInsight_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
