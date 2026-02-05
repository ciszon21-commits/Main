from django.urls import path
from . import views

app_name = 'friend_expense'

urlpatterns = [
    # 群組相關
    path('', views.GroupListView.as_view(), name='group_list'),
    path('create/', views.GroupCreateView.as_view(), name='group_create'),
    path('<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_update'),
    path('<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),
    
    # 成員相關
    path('<int:group_pk>/member/add/', views.MemberAddView.as_view(), name='member_add'),
    path('member/<int:pk>/delete/', views.MemberDeleteView.as_view(), name='member_delete'),
    
    # 記帳相關
    path('<int:group_pk>/expense/add/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expense/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expense/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # 結算
    path('<int:pk>/settlement/', views.SettlementView.as_view(), name='settlement'),
]
