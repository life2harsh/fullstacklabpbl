from django.contrib import admin
from django.db.models import Count

from reports.exports import csv_response

from .models import Comment, Mention, Poll, PollOption, PollVote, Post, Tag


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ["author", "content", "parent", "created_at"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["author", "parent"]


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "like_count", "comment_count", "created_at"]
    search_fields = ["title", "content", "author__username"]
    list_filter = ["created_at", "tags"]
    filter_horizontal = ["tags"]
    date_hierarchy = "created_at"
    inlines = [CommentInline]
    actions = ["export_csv"]

    def get_queryset(self, request):
        return super().get_queryset(request).with_stats()

    @admin.display(ordering="like_count")
    def like_count(self, post):
        return post.like_count

    @admin.display(ordering="comment_count")
    def comment_count(self, post):
        return post.comment_count

    @admin.action(description="Export selected posts to CSV")
    def export_csv(self, request, queryset):
        return csv_response("vortex-posts.csv", ["ID", "Title", "Author", "Likes", "Comments", "Created"],
                            ([p.id, p.title, p.author.username, p.like_count, p.comment_count, p.created_at.isoformat()] for p in queryset))


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "created_at"]
    search_fields = ["content", "author__username", "post__title"]
    list_filter = ["created_at"]


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["question", "post", "created_at"]
    inlines = [PollOptionInline]


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ["voter", "poll", "option", "created_at"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "post_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(post_count=Count("posts"))

    @admin.display(ordering="post_count")
    def post_count(self, tag):
        return tag.post_count


admin.site.register(Mention)
admin.site.site_header = "Vortex administration"
admin.site.site_title = "Vortex admin"
