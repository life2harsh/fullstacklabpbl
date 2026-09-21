from django.urls import path

from . import views

urlpatterns = [
    path("posts/<int:post_id>/like", views.like_post, name="like-post"),
    path("posts/<int:post_id>/repost", views.repost_post, name="repost-post"),
    path("posts/<int:post_id>/bookmark", views.bookmark_post, name="bookmark-post"),
    path("users/<int:user_id>/follow", views.follow_user, name="follow-user"),
    path("users/<int:user_id>/block", views.block_user, name="block-user"),
]
