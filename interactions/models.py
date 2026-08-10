from django.contrib.auth.models import User
from django.db import models

from posts.models import Post


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "post"), name="unique_like")]


class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reposts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reposts")
    quote_text = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "post"), name="unique_repost")]


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "post"), name="unique_bookmark")]
