import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Exists, OuterRef, Q, Value
from django.urls import reverse
from django.utils import timezone

HASHTAG = re.compile(r"(?<![&\w])#(\w{1,50})")


class PostQuerySet(models.QuerySet):
    def with_stats(self, user=None):
        from interactions.models import Bookmark, Like, Repost

        qs = self.select_related("author__profile").annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            repost_count=Count("reposts", distinct=True),
        )
        if not (user and user.is_authenticated):
            return qs.annotate(is_liked=Value(False), is_bookmarked=Value(False), is_reposted=Value(False))
        mine = {"post": OuterRef("pk"), "user": user}
        return qs.annotate(
            is_liked=Exists(Like.objects.filter(**mine)),
            is_bookmarked=Exists(Bookmark.objects.filter(**mine)),
            is_reposted=Exists(Repost.objects.filter(**mine)),
        )

    def visible_to(self, user):
        return self.exclude(Q(author__blocks_received__blocker=user) | Q(author__blocks_created__blocked=user))

    def search(self, query):
        return self.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query)) if query else self


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"#{self.name}"

    def get_absolute_url(self):
        return f"{reverse('feed')}?tag={self.name}"

    @classmethod
    def trending(cls, days=7, limit=8):
        recent = Q(posts__created_at__gte=timezone.now() - timedelta(days=days))
        return cls.objects.annotate(post_count=Count("posts", filter=recent)).filter(post_count__gt=0).order_by("-post_count", "name")[:limit]


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField(max_length=10000)
    media = models.FileField(upload_to="posts/", blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    repost_of = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="reposts_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=("-created_at",)), models.Index(fields=("title",))]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post-detail-page", args=[self.pk])

    def sync_tags(self):
        names = {name.lower() for name in HASHTAG.findall(f"{self.title} {self.content}")}
        Tag.objects.bulk_create([Tag(name=name) for name in names], ignore_conflicts=True)
        self.tags.set(Tag.objects.filter(name__in=names))


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name="replies")
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.content[:40]}"


class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="poll")
    question = models.CharField(max_length=500)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

    def results(self, user=None):
        options = list(self.options.annotate(vote_count=Count("votes")))
        total = sum(option.vote_count for option in options)
        voted = set(PollVote.objects.filter(voter=user, option__poll=self).values_list("option_id", flat=True)) if user else set()
        for option in options:
            option.percent = round(100 * option.vote_count / total) if total else 0
            option.chosen = option.id in voted
        return {"options": options, "total": total, "has_voted": bool(voted)}


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class PollVote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="poll_votes")
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("voter", "poll"), name="one_vote_per_poll")]


class Mention(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, related_name="mentions")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True, related_name="mentions")
    message_id = models.PositiveIntegerField(blank=True, null=True)
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mentions_received")
    created_at = models.DateTimeField(auto_now_add=True)
