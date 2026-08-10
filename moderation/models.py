from django.contrib.auth.models import User
from django.db import models


class Report(models.Model):
    REPORT_TYPES = [("post", "Post"), ("comment", "Comment"), ("user", "User")]
    STATUS_CHOICES = [("pending", "Pending"), ("reviewed", "Reviewed"), ("dismissed", "Dismissed")]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_filed")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    target_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=100)
    details = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
