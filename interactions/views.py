import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.models import Block, Follow
from notifications.models import Notification
from posts.models import Post

from .models import Bookmark, Like, Repost


def _body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return request.POST.dict()


@login_required
@require_http_methods(["POST", "DELETE"])
def like_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like = Like.objects.filter(user=request.user, post=post).first()
    if request.method == "POST":
        if like:
            return JsonResponse({"detail": "Already liked"}, status=400)
        Like.objects.create(user=request.user, post=post)
        if post.author != request.user:
            Notification.objects.create(recipient=post.author, actor=request.user, type="like", post=post, message=f"{request.user.username} liked your post")
        return JsonResponse({"message": "Post liked"})
    if not like:
        return JsonResponse({"detail": "Like not found"}, status=404)
    like.delete()
    return JsonResponse({"message": "Post unliked"})


@login_required
@require_http_methods(["POST", "DELETE"])
def repost_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    repost = Repost.objects.filter(user=request.user, post=post).first()
    if request.method == "POST":
        if repost and not _body(request).get("quote_text"):
            return JsonResponse({"detail": "Already reposted"}, status=400)
        if not repost:
            repost = Repost.objects.create(user=request.user, post=post, quote_text=_body(request).get("quote_text", ""))
            if post.author != request.user:
                Notification.objects.create(recipient=post.author, actor=request.user, type="repost", post=post, message=f"{request.user.username} reposted your post")
        return JsonResponse({"message": "Post reposted"})
    if not repost:
        return JsonResponse({"detail": "Repost not found"}, status=404)
    repost.delete()
    return JsonResponse({"message": "Repost removed"})


@login_required
@require_http_methods(["POST", "DELETE"])
def bookmark_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    bookmark = Bookmark.objects.filter(user=request.user, post=post).first()
    if request.method == "POST":
        if bookmark:
            return JsonResponse({"detail": "Already bookmarked"}, status=400)
        Bookmark.objects.create(user=request.user, post=post)
        return JsonResponse({"message": "Post bookmarked"})
    if not bookmark:
        return JsonResponse({"detail": "Bookmark not found"}, status=404)
    bookmark.delete()
    return JsonResponse({"message": "Bookmark removed"})


@login_required
def bookmarks(request):
    from posts.views import _post_payload

    posts = Post.objects.filter(bookmarks__user=request.user).select_related("author", "author__profile").distinct()
    return JsonResponse([_post_payload(post, request.user) for post in posts], safe=False)


@login_required
@require_http_methods(["POST", "DELETE"])
def follow_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        return JsonResponse({"detail": "Cannot follow yourself"}, status=400)
    follow = Follow.objects.filter(follower=request.user, following=target).first()
    if request.method == "POST":
        if follow:
            return JsonResponse({"detail": "Already following"}, status=400)
        Follow.objects.create(follower=request.user, following=target)
        Notification.objects.create(recipient=target, actor=request.user, type="follow", message=f"{request.user.username} followed you")
        return JsonResponse({"message": "User followed"})
    if not follow:
        return JsonResponse({"detail": "Not following"}, status=404)
    follow.delete()
    return JsonResponse({"message": "User unfollowed"})


@login_required
def followers(request, user_id):
    users = User.objects.filter(follower_links__following_id=user_id).select_related("profile")
    return JsonResponse([{"id": user.id, "username": user.username, "full_name": user.profile.full_name, "avatar_url": user.profile.avatar.url if user.profile.avatar else None} for user in users], safe=False)


@login_required
def following(request, user_id):
    users = User.objects.filter(following_links__follower_id=user_id).select_related("profile")
    return JsonResponse([{"id": user.id, "username": user.username, "full_name": user.profile.full_name, "avatar_url": user.profile.avatar.url if user.profile.avatar else None} for user in users], safe=False)


@login_required
@require_http_methods(["POST", "DELETE"])
def block_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        return JsonResponse({"detail": "Cannot block yourself"}, status=400)
    block = Block.objects.filter(blocker=request.user, blocked=target).first()
    if request.method == "POST":
        if block:
            return JsonResponse({"detail": "User already blocked"}, status=400)
        Block.objects.create(blocker=request.user, blocked=target)
        return JsonResponse({"message": "User blocked successfully"})
    if not block:
        return JsonResponse({"detail": "Block not found"}, status=404)
    block.delete()
    return JsonResponse({"message": "User unblocked successfully"})


@login_required
def blocked_users(request):
    users = User.objects.filter(blocks_received__blocker=request.user).select_related("profile")
    return JsonResponse([{"id": user.id, "username": user.username, "avatar_url": user.profile.avatar.url if user.profile.avatar else None} for user in users], safe=False)
