import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.utils import is_ajax
from moderation.forms import ReportForm
from notifications.models import Notification

from .forms import CommentForm, PollForm, PollOptionFormSet, PostForm, VoteForm
from .models import Comment, Mention, Poll, PollVote, Post

FEED_VIEWS = {"all": "Latest", "following": "Following", "trending": "Trending", "bookmarks": "Bookmarks"}


def notify_mentions(text, actor, post=None, comment=None):
    names = set(re.findall(r"@([A-Za-z0-9_]+)", text or ""))
    for user in User.objects.filter(username__in=names, profile__allow_mentions=True).exclude(pk=actor.pk):
        Mention.objects.create(mentioned_user=user, post=post, comment=comment)
        Notification.objects.create(recipient=user, actor=actor, type="mention", post=post, comment=comment, message=f"{actor.username} mentioned you")


def _feed(request, view, query):
    posts = Post.objects.visible_to(request.user).search(query).with_stats(request.user).select_related("poll").order_by("-created_at")
    if view == "following":
        posts = posts.filter(Q(author__follower_links__follower=request.user) | Q(author=request.user))
    elif view == "bookmarks":
        posts = posts.filter(bookmarks__user=request.user)
    elif view == "trending":
        posts = posts.filter(created_at__gte=timezone.now() - timedelta(days=7)).annotate(
            score=F("like_count") + 2 * F("comment_count") + 3 * F("repost_count")
        ).order_by("-score", "-created_at")
    return posts


def _save_post(request, form, poll_form, options):
    if not (form.is_valid() and poll_form.is_valid() and options.is_valid()):
        return None
    question = poll_form.cleaned_data.get("question", "").strip()
    filled = [f for f in options.forms if f.cleaned_data.get("text", "").strip()]
    if question and len(filled) < 2:
        poll_form.add_error("question", "A poll needs at least two options.")
        return None
    if filled and not question:
        poll_form.add_error("question", "Add a question for your poll options.")
        return None
    with transaction.atomic():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        if question:
            poll = poll_form.save(commit=False)
            poll.post = post
            poll.save()
            options.instance = poll
            options.save()
    notify_mentions(post.content, request.user, post=post)
    return post


@login_required
def feed_page(request):
    view = request.GET.get("view") if request.GET.get("view") in FEED_VIEWS else "all"
    query = request.GET.get("q", "").strip()
    form = PostForm(request.POST or None, request.FILES or None)
    poll_form = PollForm(request.POST or None, prefix="poll")
    options = PollOptionFormSet(request.POST or None, instance=Poll(), prefix="option")
    if request.method == "POST":
        post = _save_post(request, form, poll_form, options)
        if post:
            messages.success(request, "Post published.")
            return redirect(post)
    page = Paginator(_feed(request, view, query), 10).get_page(request.GET.get("page"))
    context = {
        "page": page,
        "view": view,
        "views": FEED_VIEWS,
        "query": query,
        "people": User.objects.filter(Q(username__icontains=query) | Q(profile__full_name__icontains=query), is_active=True).select_related("profile")[:6] if query else [],
        "form": form,
        "poll_form": poll_form,
        "options": options,
        "compose_open": request.method == "POST",
    }
    return render(request, "partials/_feed_results.html" if is_ajax(request) else "feed.html", context)


def _comment_tree(post):
    comments = list(post.comments.select_related("author__profile"))
    children = {}
    for comment in comments:
        children.setdefault(comment.parent_id, []).append(comment)
    for comment in comments:
        comment.children = children.get(comment.id, [])
    return children.get(None, [])


@login_required
def post_detail_page(request, post_id):
    post = get_object_or_404(Post.objects.visible_to(request.user).with_stats(request.user), pk=post_id)
    form = CommentForm(request.POST or None, post=post)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.post, comment.author = post, request.user
        comment.save()
        recipients = {post.author, comment.parent.author if comment.parent else post.author} - {request.user}
        Notification.objects.bulk_create([
            Notification(recipient=user, actor=request.user, type="comment", post=post, comment=comment,
                         message=f"{request.user.username} {'replied to your comment' if comment.parent and user == comment.parent.author else 'commented on your post'}")
            for user in recipients
        ])
        notify_mentions(comment.content, request.user, post=post, comment=comment)
        return redirect(f"{post.get_absolute_url()}#comment-{comment.pk}")
    poll = getattr(post, "poll", None)
    return render(request, "post.html", {
        "post": post,
        "comments": _comment_tree(post),
        "form": form,
        "poll": poll,
        "poll_results": poll.results(request.user) if poll else None,
        "vote_form": VoteForm(poll=poll) if poll else None,
        "report_form": ReportForm(),
    })


def _owned(request, owner):
    return owner == request.user or request.user.is_staff


@login_required
def post_edit_page(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not _owned(request, post.author):
        return HttpResponseForbidden("You can only edit your own posts.")
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Post updated.")
        return redirect(post)
    return render(request, "post-edit.html", {"form": form, "post": post})


@login_required
@require_POST
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not _owned(request, post.author):
        return HttpResponseForbidden("You can only delete your own posts.")
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect("feed")


@login_required
@require_POST
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=comment_id)
    if not _owned(request, comment.author):
        return HttpResponseForbidden("You can only delete your own comments.")
    comment.delete()
    return redirect(comment.post)


@login_required
@require_POST
def vote_poll(request, poll_id):
    poll = get_object_or_404(Poll.objects.select_related("post"), pk=poll_id)
    form = VoteForm(request.POST, poll=poll)
    if form.is_valid():
        PollVote.objects.update_or_create(voter=request.user, poll=poll, defaults={"option": form.cleaned_data["option"]})
    return redirect(poll.post)
