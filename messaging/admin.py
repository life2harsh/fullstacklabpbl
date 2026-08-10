from django.contrib import admin

from .models import Conversation, ConversationParticipant, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at"]
    search_fields = ["participants__username"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "conversation", "message", "timestamp", "read_status"]
    search_fields = ["sender__username", "message"]
    list_filter = ["read_status", "timestamp"]


admin.site.register(ConversationParticipant)
