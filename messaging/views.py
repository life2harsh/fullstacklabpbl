from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from core.utils import avatar_url, json_body

from .models import Conversation, ConversationParticipant, Message


def _conversation_for(first, second, create=True):
    conversation = Conversation.objects.filter(participants=first).filter(participants=second).first()
    if not conversation and create:
        conversation = Conversation.objects.create()
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(conversation=conversation, user=first),
            ConversationParticipant(conversation=conversation, user=second),
        ])
    return conversation


@login_required
def chat_page(request):
    return render(request, "chat.html", {"me": {"id": request.user.id, "username": request.user.username}})


def _message_payload(message):
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.conversation.participants.exclude(pk=message.sender_id).values_list("id", flat=True).first(),
        "message": message.message or None,
        "media_url": message.media.url if message.media else None,
        "timestamp": message.timestamp.isoformat(),
        "read_status": message.read_status,
        "sender_username": message.sender.username,
    }


@login_required
@require_http_methods(["POST"])
def send_message(request):
    receiver_id = request.POST.get("receiver_id")
    receiver = get_object_or_404(User, pk=receiver_id)
    text = request.POST.get("message", "").strip()
    media = request.FILES.get("media")
    if not text and not media:
        return JsonResponse({"detail": "Message must contain text or media"}, status=400)
    conversation = _conversation_for(request.user, receiver)
    message = Message.objects.create(conversation=conversation, sender=request.user, message=text, media=media)
    return JsonResponse(_message_payload(message), status=201)


@login_required
def conversations(request):
    result = []
    for conversation in Conversation.objects.filter(participants=request.user).prefetch_related("participants__profile"):
        other = next((user for user in conversation.participants.all() if user.pk != request.user.pk), None)
        if not other:
            continue
        last = conversation.messages.select_related("sender").order_by("-timestamp").first()
        result.append({
            "other_user_id": other.id,
            "username": other.username,
            "avatar_url": avatar_url(other),
            "last_message_time": last.timestamp.isoformat() if last else None,
            "last_message": last.message if last else None,
            "last_message_sender_id": last.sender_id if last else None,
            "unread_count": conversation.messages.filter(read_status=False).exclude(sender=request.user).count(),
        })
    return JsonResponse(result, safe=False)


@login_required
def conversation_messages(request, other_user_id):
    other = get_object_or_404(User, pk=other_user_id)
    conversation = _conversation_for(request.user, other, create=False)
    if not conversation:
        return JsonResponse([], safe=False)
    if request.method == "GET":
        messages = conversation.messages.select_related("sender").all()
        conversation.messages.filter(sender=other, read_status=False).update(read_status=True)
        return JsonResponse([_message_payload(message) for message in messages], safe=False)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


@login_required
@require_http_methods(["DELETE"])
def clear_conversation(request, other_user_id):
    other = get_object_or_404(User, pk=other_user_id)
    conversation = _conversation_for(request.user, other, create=False)
    if conversation:
        conversation.messages.all().delete()
    return JsonResponse({"message": "Conversation cleared successfully"})


@login_required
@require_http_methods(["PUT", "DELETE"])
def message_detail(request, message_id):
    message = get_object_or_404(Message.objects.select_related("sender", "conversation"), pk=message_id)
    if message.sender != request.user:
        return JsonResponse({"detail": "Not authorized"}, status=403)
    if request.method == "DELETE":
        message.delete()
        return JsonResponse({"message": "Message deleted successfully"})
    data = json_body(request)
    message.message = data.get("message", message.message)
    message.save(update_fields=["message"])
    return JsonResponse(_message_payload(message))


@login_required
def message_or_conversation(request, identifier):
    if request.method == "GET":
        return conversation_messages(request, identifier)
    return message_detail(request, identifier)
