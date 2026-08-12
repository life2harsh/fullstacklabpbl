from django.urls import path

from . import views

urlpatterns = [
    path("posts/<int:post_id>/like", views.like_post, name="like-post"),
    path("posts/<int:post_id>/repost", views.repost_post, name="repost-post"),
    path("posts/<int:post_id>/bookmark", views.bookmark_post, name="bookmark-post"),
    path("bookmarks", views.bookmarks, name="bookmarks"),
    path("users/<int:user_id>/follow", views.follow_user, name="follow-user"),
    path("users/<int:user_id>/followers", views.followers, name="followers"),
    path("users/<int:user_id>/following", views.following, name="following"),
    path("users/block/<int:user_id>", views.block_user, name="block-user"),
    path("users/blocked", views.blocked_users, name="blocked-users"),
]
