from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "actor", "type", "read_status", "created_at"]
    search_fields = ["recipient__username", "actor__username", "message"]
    list_filter = ["type", "read_status", "created_at"]
    ordering = ["-created_at"]
