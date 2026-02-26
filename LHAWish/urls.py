from django.urls import path
from . import views

app_name = 'lhawish'

urlpatterns = [
    # 主頁（研發專案列表）
    path('', views.DashboardView.as_view(), name='dashboard'),

    # 分頁列表
    path('market/', views.MarketListView.as_view(), name='market_list'),
    path('gossip/', views.GossipListView.as_view(), name='gossip_list'),
    path('mailbox/', views.MailboxView.as_view(), name='mailbox'),
    path('manager/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),

    # 貼文 CRUD
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),

    # AJAX API
    path('api/like/<int:pk>/', views.toggle_like, name='toggle_like'),
    path('api/save/<int:pk>/', views.toggle_save, name='toggle_save'),
    path('api/comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('api/status/<int:pk>/', views.update_status, name='update_status'),
    path('api/comment-like/<int:pk>/', views.toggle_comment_like, name='toggle_comment_like'),
    path('api/comment/<int:pk>/edit/', views.edit_comment, name='edit_comment'),
    path('api/comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('api/settings/', views.save_settings, name='save_settings'),
    path('api/market/<int:pk>/sold/', views.mark_sold, name='mark_sold'),

    # 園路願望
    path('petition/', views.PetitionListView.as_view(), name='petition_list'),
    path('petition/<int:pk>/', views.PetitionDetailView.as_view(), name='petition_detail'),
    path('petition/create/', views.PetitionCreateView.as_view(), name='petition_create'),
    path('petition/api/endorse/<int:pk>/', views.endorse_petition, name='endorse_petition'),
    path('petition/api/withdraw/<int:pk>/', views.withdraw_petition, name='withdraw_petition'),
    path('petition/api/respond/<int:pk>/', views.respond_petition, name='respond_petition'),
    path('petition/api/comment/<int:pk>/', views.add_petition_comment, name='add_petition_comment'),
    path('petition/api/status/<int:pk>/', views.update_petition_status, name='update_petition_status'),
    path('petition/api/save/<int:pk>/', views.toggle_petition_save, name='toggle_petition_save'),
    path('petition/api/edit/<int:pk>/', views.edit_petition, name='edit_petition'),
    path('petition/api/action/<int:pk>/', views.petition_action, name='petition_action'),
    path('petition/api/delete-response/<int:pk>/', views.delete_petition_response, name='delete_petition_response'),
]
