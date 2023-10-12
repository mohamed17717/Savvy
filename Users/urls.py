from django.urls import path

from knox import views as knox_views

from Users import views


app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='knox_login'),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('otp-ask/', views.AskForOTPCodeAPI.as_view(), name='otp_ask'),
]
