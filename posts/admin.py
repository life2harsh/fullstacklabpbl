from django.contrib import admin

from .models import Comment, Mention, Poll, PollOption, PollVote, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at", "updated_at"]
    search_fields = ["title", "content", "author__username"]
    list_filter = ["created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "created_at"]
    search_fields = ["content", "author__username", "post__title"]
    list_filter = ["created_at"]


admin.site.register([Poll, PollOption, PollVote, Mention])
