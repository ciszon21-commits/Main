from django.urls import path
from . import views

app_name = 'aitoolshub'

urlpatterns = [
    # 列表頁
    path('', views.AIToolListView.as_view(), name='tool_list'),

    # 我的收藏
    path('my-favorites/', views.MyFavoritesView.as_view(), name='my_favorites'),

    # 新增工具
    path('create/', views.AIToolCreateView.as_view(), name='tool_create'),

    # 工具詳細頁
    path('<int:pk>/', views.AIToolDetailView.as_view(), name='tool_detail'),

    # 編輯工具
    path('<int:pk>/edit/', views.AIToolUpdateView.as_view(), name='tool_update'),

    # 刪除工具
    path('<int:pk>/delete/', views.AIToolDeleteView.as_view(), name='tool_delete'),

    # 收藏/取消收藏 (AJAX)
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),

    # 點讚/取消點讚 (AJAX)
    path('<int:pk>/like/', views.toggle_like, name='toggle_like'),

    # 新增留言 (AJAX)
    path('<int:pk>/comment/', views.comment_create, name='comment_create'),

    # 回覆留言 (AJAX)
    path('comment/<int:pk>/reply/', views.reply_create, name='reply_create'),

    # 編輯留言 (AJAX)
    path('comment/<int:pk>/edit/', views.comment_update, name='comment_update'),

    # 留言反應 (AJAX)
    path('comment/<int:pk>/reaction/', views.toggle_comment_reaction, name='toggle_comment_reaction'),

    # 刪除留言 (AJAX)
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
]

