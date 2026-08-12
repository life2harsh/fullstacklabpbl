from django.urls import path

from . import views

urlpatterns = [
    path("feed/", views.feed_page, name="feed"),
    path("post/", views.post_page, name="post-page"),
    path("profile/", views.profile_page, name="profile-page"),
    path("public-profile/", views.public_profile_page, name="public-profile-page"),
    path("search/", views.search, name="search"),
    path("trending", views.trending, name="trending"),
    path("posts", views.posts_collection, name="posts"),
    path("posts/<int:post_id>/comments", views.post_comments, name="post-comments"),
    path("posts/<int:post_id>/poll", views.create_poll, name="create-poll"),
    path("polls/<int:poll_id>/vote", views.vote_poll, name="vote-poll"),
    path("posts/<int:post_id>", views.post_detail, name="post-detail"),
    path("comments/<int:comment_id>", views.delete_comment, name="delete-comment"),
    path("users/<int:user_id>/posts", views.user_posts, name="user-posts"),
]
