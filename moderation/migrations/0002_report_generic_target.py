import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

MODELS = {"post": ("posts", "post"), "comment": ("posts", "comment"), "user": ("auth", "user")}


def to_content_type(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Report = apps.get_model("moderation", "Report")
    for report in Report.objects.all():
        app_label, model = MODELS.get(report.report_type, MODELS["post"])
        report.content_type = ContentType.objects.get_or_create(app_label=app_label, model=model)[0]
        report.save(update_fields=["content_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("moderation", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name="report", name="content_type", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype")),
        migrations.RunPython(to_content_type, migrations.RunPython.noop),
        migrations.RemoveField(model_name="report", name="report_type"),
        migrations.RenameField(model_name="report", old_name="target_id", new_name="object_id"),
        migrations.AlterField(model_name="report", name="content_type", field=models.ForeignKey(limit_choices_to={"model__in": ("post", "comment", "user")}, on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype")),
        migrations.AlterField(model_name="report", name="reason", field=models.CharField(choices=[("spam", "Spam"), ("harassment", "Harassment"), ("hate", "Hate speech"), ("misinformation", "Misinformation"), ("other", "Other")], max_length=100)),
        migrations.AlterField(model_name="report", name="status", field=models.CharField(choices=[("pending", "Pending"), ("reviewed", "Reviewed"), ("dismissed", "Dismissed"), ("removed", "Content removed")], default="pending", max_length=50)),
        migrations.AddIndex(model_name="report", index=models.Index(fields=["content_type", "object_id"], name="moderation__content_408935_idx")),
        migrations.AddConstraint(model_name="report", constraint=models.UniqueConstraint(fields=("reporter", "content_type", "object_id"), name="one_report_per_target")),
    ]
