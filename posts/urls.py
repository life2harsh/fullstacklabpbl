from django.urls import path

from . import views

urlpatterns = [
    path("feed/", views.feed_page, name="feed"),
    path("post/<int:post_id>/", views.post_detail_page, name="post-detail-page"),
    path("post/<int:post_id>/edit/", views.post_edit_page, name="post-edit"),
    path("post/<int:post_id>/delete/", views.post_delete, name="post-delete"),
    path("comments/<int:comment_id>/delete/", views.comment_delete, name="comment-delete"),
    path("polls/<int:poll_id>/vote/", views.vote_poll, name="vote-poll"),
]
