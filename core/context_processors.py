from messaging.models import Message
from notifications.models import Notification


def unread_counts(user):
    return {
        "notifications": Notification.objects.filter(recipient=user, read_status=False).count(),
        "messages": Message.objects.filter(conversation__participants=user, read_status=False).exclude(sender=user).values("conversation").distinct().count(),
    }


def badges(request):
    if not request.user.is_authenticated:
        return {}
    return {"badges": unread_counts(request.user)}
