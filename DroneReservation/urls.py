from django.urls import path
from . import views

app_name = 'drone'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # 預約申請 CRUD
    path('apply/', views.ReservationCreateView.as_view(), name='reservation_create'),
    path('<int:pk>/', views.ReservationDetailView.as_view(), name='reservation_detail'),
    path('<int:pk>/edit/', views.ReservationUpdateView.as_view(), name='reservation_update'),
    path('<int:pk>/cancel/', views.cancel_reservation, name='reservation_cancel'),
    
    # 申請人管理頁面
    path('my-reservations/', views.MyReservationsView.as_view(), name='my_reservations'),
    
    # 簽核人管理頁面
    path('pending/', views.PendingApprovalsView.as_view(), name='pending_approvals'),
    path('<int:pk>/review/', views.review_reservation, name='review_reservation'),
    
    # 公告管理（僅限簽核人）
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('announcements/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('announcements/<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path('announcements/<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
    
    # API
    path('api/events/', views.calendar_events_api, name='calendar_events'),
    
    # 系統設定（僅限管理簽核人）
    path('settings/', views.SettingsView.as_view(), name='settings'),
    
    # 簽核人取消已核准預約
    path('<int:pk>/reviewer-cancel/', views.reviewer_cancel_reservation, name='reviewer_cancel_reservation'),
]

