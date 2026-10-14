from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

RESET = {"template_name": "registration/password-reset.html"}

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.home, name="login-page"),
    path("signup", views.register, name="signup"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(**RESET), name="password_reset"),
    path("password-reset/sent/", auth_views.PasswordResetDoneView.as_view(**RESET), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(**RESET), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(**RESET), name="password_reset_complete"),
    path("profile/", views.profile_page, name="profile-page"),
    path("profile/delete/", views.delete_account, name="delete-account"),
    path("people/<int:user_id>/", views.public_profile_page, name="public-profile-page"),
    path("users/me", views.me, name="me"),
    path("users/mentionable", views.mentionable_users, name="mentionable-users"),
    path("users/<int:user_id>", views.user_detail, name="user-detail"),
]
