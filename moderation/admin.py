from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["reporter", "report_type", "target_id", "reason", "status", "created_at"]
    search_fields = ["reporter__username", "reason", "details"]
    list_filter = ["report_type", "status", "created_at"]
    ordering = ["status", "-created_at"]
