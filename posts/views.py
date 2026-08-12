import json
import re
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accounts.models import Block
from notifications.models import Notification

from .forms import CommentForm, PostForm
from .models import Comment, Mention, Poll, PollOption, PollVote, Post


def _post_payload(post, user=None):
    return {
        "id": post.id,
        "user_id": post.author_id,
        "title": post.title,
        "content": post.content,
        "media_url": post.media.url if post.media else None,
        "repost_of": post.repost_of_id,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "author_username": post.author.username,
        "author_avatar_url": post.author.profile.avatar.url if getattr(post.author, "profile", None) and post.author.profile.avatar else None,
        "like_count": post.likes.count(),
        "comment_count": post.comments.count(),
        "repost_count": post.reposts.count(),
        "is_liked": bool(user and post.likes.filter(user=user).exists()),
        "is_reposted": bool(user and post.reposts.filter(user=user).exists()),
        "is_bookmarked": bool(user and post.bookmarks.filter(user=user).exists()),
    }


def _comment_payload(comment):
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "user_id": comment.author_id,
        "parent_comment_id": comment.parent_id,
        "parent_username": comment.parent.author.username if comment.parent else None,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
        "author_username": comment.author.username,
        "author_avatar_url": comment.author.profile.avatar.url if getattr(comment.author, "profile", None) and comment.author.profile.avatar else None,
        "like_count": 0,
        "reply_count": comment.replies.count(),
    }


def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return request.POST.dict()


def _notify_mentions(text, post=None, comment=None, actor=None):
    for username in set(re.findall(r"@([A-Za-z0-9_]+)", text or "")):
        mentioned = User.objects.filter(username__iexact=username, profile__allow_mentions=True).first()
        if mentioned and mentioned != actor:
            Mention.objects.create(mentioned_user=mentioned, post=post, comment=comment)
            Notification.objects.create(
                recipient=mentioned,
                actor=actor,
                type="mention",
                post=post,
                comment=comment,
                message="You were mentioned",
            )


@login_required
def feed_page(request):
    return render(request, "feed.html")


@login_required
def post_page(request):
    return render(request, "post.html")


@login_required
def profile_page(request):
    return render(request, "profile.html")


@login_required
def public_profile_page(request):
    return render(request, "public-profile.html")


@login_required
@require_http_methods(["GET", "POST"])
def posts_collection(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        _notify_mentions(post.content, post=post, actor=request.user)
        return JsonResponse(_post_payload(post, request.user), status=201)

    query = request.GET.get("search", "").strip()
    posts = Post.objects.select_related("author", "author__profile").prefetch_related("likes", "comments", "reposts", "bookmarks")
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query))
    blocked_ids = Block.objects.filter(blocker=request.user).values_list("blocked_id", flat=True)
    posts = posts.exclude(author_id__in=blocked_ids)[:50]
    return JsonResponse([_post_payload(post, request.user) for post in posts], safe=False)


@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related("author", "author__profile"), pk=post_id)
    if request.method == "GET":
        return JsonResponse(_post_payload(post, request.user))
    if post.author != request.user and not request.user.is_staff:
        return JsonResponse({"detail": "Not authorized"}, status=403)
    if request.method == "DELETE":
        post.delete()
        return JsonResponse({"message": "Post deleted successfully"})
    data = _json_body(request)
    update_data = {"title": data.get("title", post.title), "content": data.get("content", post.content)}
    form = PostForm(update_data, instance=post)
    if not form.is_valid():
        return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
    form.save()
    return JsonResponse(_post_payload(post, request.user))


@login_required
@require_http_methods(["GET", "POST"])
def post_comments(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "GET":
        comments = Comment.objects.filter(post=post).select_related("author", "author__profile", "parent", "parent__author")
        return JsonResponse([_comment_payload(comment) for comment in comments], safe=False)
    data = _json_body(request)
    form = CommentForm(data)
    if not form.is_valid():
        return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    if post.author != request.user:
        Notification.objects.create(recipient=post.author, actor=request.user, type="comment", post=post, comment=comment, message=f"{request.user.username} commented on your post")
    if comment.parent and comment.parent.author != request.user:
        Notification.objects.create(recipient=comment.parent.author, actor=request.user, type="comment", post=post, comment=comment, message=f"{request.user.username} replied to your comment")
    _notify_mentions(comment.content, post=post, comment=comment, actor=request.user)
    return JsonResponse(_comment_payload(comment), status=201)


@login_required
@require_http_methods(["DELETE"])
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user and not request.user.is_staff:
        return JsonResponse({"detail": "Not authorized"}, status=403)
    comment.delete()
    return JsonResponse({"message": "Comment deleted successfully"})


@login_required
def user_posts(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return JsonResponse([_post_payload(post, request.user) for post in Post.objects.filter(author=user).select_related("author", "author__profile")], safe=False)


@login_required
def trending(request):
    since = timezone.now() - timedelta(days=1)
    posts = Post.objects.filter(created_at__gte=since).annotate(score=Count("likes") + 2 * Count("comments") + 3 * Count("reposts")).order_by("-score", "-created_at")[:20]
    return JsonResponse([_post_payload(post, request.user) for post in posts.select_related("author", "author__profile")], safe=False)


def search(request):
    query = request.GET.get("q", "").strip()
    posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).select_related("author")[:10] if query else Post.objects.none()
    users = User.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query)).select_related("profile")[:10] if query else User.objects.none()
    return JsonResponse({"posts": [_post_payload(post, request.user if request.user.is_authenticated else None) for post in posts], "users": [{"id": user.id, "username": user.username, "full_name": user.profile.full_name} for user in users]})


@login_required
@require_http_methods(["POST"])
def create_poll(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    data = _json_body(request)
    options = [str(option).strip() for option in data.get("options", []) if str(option).strip()]
    if not data.get("question", "").strip() or len(options) < 2:
        return JsonResponse({"detail": "A poll needs a question and at least two options"}, status=400)
    poll = Poll.objects.create(post=post, question=data["question"].strip())
    PollOption.objects.bulk_create([PollOption(poll=poll, text=option) for option in options[:6]])
    return JsonResponse({"id": poll.id, "question": poll.question, "options": [{"id": option.id, "text": option.text, "votes": 0} for option in poll.options.all()]}, status=201)


@login_required
@require_http_methods(["POST"])
def vote_poll(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    option_id = _json_body(request).get("option_id")
    option = get_object_or_404(PollOption, pk=option_id, poll=poll)
    PollVote.objects.filter(voter=request.user, option__poll=poll).delete()
    PollVote.objects.create(voter=request.user, option=option)
    return JsonResponse({"message": "Vote recorded", "option_id": option.id})
