from django.urls import path, include

from . import views


app_name = 'home'


urlpatterns = [
    # Base
    path('', views.HomeView.as_view(), name='home'),
    # Auth
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('accounts/login/', views.LoginView.as_view(), name='account-login'),
]


