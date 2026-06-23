from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("password/change/", views.change_password, name="change_password"),

    # Password reset flow (uses Core templates)
    path("password/reset/", auth_views.PasswordResetView.as_view(
        template_name="Accounts_Module/password_reset.html",
        email_template_name="Accounts_Module/password_reset_email.html",
        subject_template_name="Accounts_Module/password_reset_subject.txt",
        success_url="/accounts/password/reset/done/"), name="password_reset"),
    path("password/reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="Accounts_Module/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="Accounts_Module/password_reset_confirm.html",
        success_url="/accounts/reset/done/"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="Accounts_Module/password_reset_complete.html"), name="password_reset_complete"),
]
