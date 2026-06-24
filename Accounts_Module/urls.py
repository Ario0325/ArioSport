from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("password/change/", views.change_password, name="change_password"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),

    # Password reset flow (OTP-based)
    path("password/reset/", views.password_reset_request, name="password_reset"),
    path("password/reset/new/", views.password_reset_set_new, name="password_reset_set_new"),
]
