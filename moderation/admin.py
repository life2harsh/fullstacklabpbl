from django.contrib import admin

from reports.exports import csv_response

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "reporter", "content_type", "object_id", "target", "reason", "status", "created_at"]
    search_fields = ["reporter__username", "details"]
    list_filter = ["status", "reason", "content_type", "created_at"]
    ordering = ["status", "-created_at"]
    actions = ["mark_reviewed", "dismiss", "remove_content", "export_csv"]

    @admin.action(description="Mark selected as reviewed")
    def mark_reviewed(self, request, queryset):
        queryset.update(status="reviewed")

    @admin.action(description="Dismiss selected reports")
    def dismiss(self, request, queryset):
        queryset.update(status="dismissed")

    @admin.action(description="Remove reported content")
    def remove_content(self, request, queryset):
        for report in queryset:
            report.resolve("remove")

    @admin.action(description="Export selected to CSV")
    def export_csv(self, request, queryset):
        rows = ([r.id, r.reporter.username, r.content_type.model, r.object_id, r.get_reason_display(), r.status, r.created_at.isoformat()] for r in queryset.select_related("reporter", "content_type"))
        return csv_response("vortex-reports.csv", ["ID", "Reporter", "Type", "Target ID", "Reason", "Status", "Created"], rows)
