from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Report(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("reviewed", "Reviewed"), ("dismissed", "Dismissed"), ("removed", "Content removed")]
    REASONS = [("spam", "Spam"), ("harassment", "Harassment"), ("hate", "Hate speech"), ("misinformation", "Misinformation"), ("other", "Other")]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_filed")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={"model__in": ("post", "comment", "user")})
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    reason = models.CharField(max_length=100, choices=REASONS)
    details = models.TextField(max_length=1000, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=("content_type", "object_id"))]
        constraints = [models.UniqueConstraint(fields=("reporter", "content_type", "object_id"), name="one_report_per_target")]

    def __str__(self):
        return f"{self.get_reason_display()} report on {self.content_type.model} #{self.object_id}"

    def siblings(self):
        return Report.objects.filter(content_type=self.content_type, object_id=self.object_id)

    def resolve(self, action):
        if action == "remove":
            target = self.target
            if isinstance(target, User):
                target.is_active = False
                target.save(update_fields=["is_active"])
            elif target is not None:
                target.delete()
            return self.siblings().update(status="removed")
        status = {"review": "reviewed", "dismiss": "dismissed"}[action]
        return Report.objects.filter(pk=self.pk).update(status=status)
