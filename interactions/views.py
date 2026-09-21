from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from accounts.models import Block, Follow
from notifications.models import Notification
from posts.models import Post

from .models import Bookmark, Like, Repost


def _toggle(model, **lookup):
    obj, created = model.objects.get_or_create(**lookup)
    if not created:
        obj.delete()
    return created


def _notify(created, recipient, actor, kind, verb, post=None):
    if created and recipient != actor:
        Notification.objects.create(recipient=recipient, actor=actor, type=kind, post=post, message=f"{actor.username} {verb}")


def _post_toggle(model, kind=None, verb=""):
    @login_required
    @require_POST
    def view(request, post_id):
        post = get_object_or_404(Post.objects.visible_to(request.user), pk=post_id)
        active = _toggle(model, user=request.user, post=post)
        if kind:
            _notify(active, post.author, request.user, kind, verb, post)
        return JsonResponse({"active": active, "count": model.objects.filter(post=post).count()})
    return view


like_post = _post_toggle(Like, "like", "liked your post")
repost_post = _post_toggle(Repost, "repost", "reposted your post")
bookmark_post = _post_toggle(Bookmark)


@login_required
@require_POST
def follow_user(request, user_id):
    target = get_object_or_404(User, pk=user_id, is_active=True)
    if target == request.user or Block.objects.filter(Q(blocker=target, blocked=request.user) | Q(blocker=request.user, blocked=target)).exists():
        return JsonResponse({"detail": "You can't follow this user."}, status=400)
    active = _toggle(Follow, follower=request.user, following=target)
    _notify(active, target, request.user, "follow", "followed you")
    return JsonResponse({"active": active, "count": target.follower_links.count()})


@login_required
@require_POST
def block_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        return JsonResponse({"detail": "You can't block yourself."}, status=400)
    active = _toggle(Block, blocker=request.user, blocked=target)
    if active:
        Follow.objects.filter(Q(follower=request.user, following=target) | Q(follower=target, following=request.user)).delete()
    return JsonResponse({"active": active})
