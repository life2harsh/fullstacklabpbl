from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.home, name="login-page"),
    path("signup", views.register, name="signup"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("users/me", views.me, name="me"),
    path("users/me/avatar", views.upload_avatar, name="upload-avatar"),
    path("users/me/change-password", views.change_password, name="change-password"),
    path("users/search", views.search_users, name="search-users"),
    path("users/mentionable", views.mentionable_users, name="mentionable-users"),
    path("users/<int:user_id>", views.public_profile, name="public-profile"),
]
