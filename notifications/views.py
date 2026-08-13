from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import Notification


@login_required
def notifications_page(request):
    return render(request, "notifications.html")


def _payload(notification):
    return {
        "id": notification.id,
        "user_id": notification.recipient_id,
        "type": notification.type,
        "from_user_id": notification.actor_id,
        "post_id": notification.post_id,
        "comment_id": notification.comment_id,
        "message": notification.message,
        "read_status": int(notification.read_status),
        "created_at": notification.created_at.isoformat(),
        "from_username": notification.actor.username,
        "from_avatar_url": notification.actor.profile.avatar.url if notification.actor.profile.avatar else None,
    }


@login_required
def notifications(request):
    items = Notification.objects.filter(recipient=request.user).select_related("actor", "actor__profile")[:50]
    return JsonResponse([_payload(item) for item in items], safe=False)


@login_required
@require_http_methods(["PUT", "POST"])
def mark_read(request, notification_id):
    item = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    item.read_status = True
    item.save(update_fields=["read_status"])
    return JsonResponse({"message": "Notification marked as read"})


@login_required
@require_http_methods(["PUT", "POST"])
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, read_status=False).update(read_status=True)
    return JsonResponse({"message": "All notifications marked as read"})
