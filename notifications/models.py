from django.contrib.auth.models import User
from django.db import models

from posts.models import Comment, Post


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications_sent")
    type = models.CharField(max_length=50)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, related_name="notifications")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True, related_name="notifications")
    message = models.CharField(max_length=500, blank=True)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
