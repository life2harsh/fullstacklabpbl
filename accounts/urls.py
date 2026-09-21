from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.home, name="login-page"),
    path("signup", views.register, name="signup"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("profile/", views.profile_page, name="profile-page"),
    path("profile/delete/", views.delete_account, name="delete-account"),
    path("people/<int:user_id>/", views.public_profile_page, name="public-profile-page"),
    path("users/me", views.me, name="me"),
    path("users/mentionable", views.mentionable_users, name="mentionable-users"),
    path("users/<int:user_id>", views.user_detail, name="user-detail"),
]
