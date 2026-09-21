import django.db.models.deletion
from django.db import migrations, models


def fill_poll(apps, schema_editor):
    PollVote = apps.get_model("posts", "PollVote")
    seen = set()
    for vote in PollVote.objects.select_related("option").order_by("-created_at"):
        key = (vote.voter_id, vote.option.poll_id)
        if key in seen:
            vote.delete()
            continue
        seen.add(key)
        vote.poll_id = vote.option.poll_id
        vote.save(update_fields=["poll"])


class Migration(migrations.Migration):
    dependencies = [("posts", "0002_mention")]

    operations = [
        migrations.RemoveConstraint(model_name="pollvote", name="unique_poll_vote"),
        migrations.AddField(model_name="pollvote", name="poll", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="posts.poll")),
        migrations.RunPython(fill_poll, migrations.RunPython.noop),
        migrations.AlterField(model_name="pollvote", name="poll", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="posts.poll")),
        migrations.AddConstraint(model_name="pollvote", constraint=models.UniqueConstraint(fields=("voter", "poll"), name="one_vote_per_poll")),
    ]
