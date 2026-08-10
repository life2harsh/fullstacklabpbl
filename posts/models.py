from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField(max_length=10000)
    media = models.FileField(upload_to="posts/", blank=True, null=True)
    repost_of = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="reposts_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=("-created_at",)), models.Index(fields=("title",))]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name="replies")
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="poll")
    question = models.CharField(max_length=500)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)


class PollVote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="poll_votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("voter", "option"), name="unique_poll_vote")]


class Mention(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, related_name="mentions")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True, related_name="mentions")
    message_id = models.PositiveIntegerField(blank=True, null=True)
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mentions_received")
    created_at = models.DateTimeField(auto_now_add=True)
