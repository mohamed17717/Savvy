from django.urls import path

from Users import views

app_name = "users"

urlpatterns = [
    path("register/", views.RegisterAPI.as_view(), name="register"),
    path("login/", views.LoginAPI.as_view(), name="knox_login"),
    path("logout/", views.LogoutAPI.as_view(), name="knox_logout"),
    path("logoutall/", views.LogoutAllAPI.as_view(), name="knox_logoutall"),
    path("reset-password/", views.ResetPasswordAPI.as_view(), name="reset_password"),
    path("otp-ask/", views.AskForOTPCodeAPI.as_view(), name="otp_ask"),
    path(
        "profile/",
        views.UserProfileAPI.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update"}
        ),
        name="profile",
    ),
]
