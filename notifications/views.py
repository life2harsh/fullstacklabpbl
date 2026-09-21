from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notifications_page(request):
    items = Notification.objects.filter(recipient=request.user).select_related("actor__profile", "post")[:50]
    return render(request, "notifications.html", {"notifications": items})


@login_required
@require_POST
def open_notification(request, notification_id):
    item = get_object_or_404(Notification.objects.select_related("post"), pk=notification_id, recipient=request.user)
    if not item.read_status:
        item.read_status = True
        item.save(update_fields=["read_status"])
    if item.post_id:
        url = item.post.get_absolute_url()
        return redirect(f"{url}#comment-{item.comment_id}" if item.comment_id else url)
    return redirect("public-profile-page", item.actor_id)


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, read_status=False).update(read_status=True)
    return redirect("notifications-page")
