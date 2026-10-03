import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Follow
from interactions.models import Bookmark, Like, Repost
from messaging.models import Conversation, Message
from moderation.models import Report
from notifications.models import Notification
from posts.models import Comment, Poll, PollVote, Post

PEOPLE = [("aarav", "Aarav Mehta"), ("diya", "Diya Sharma"), ("kabir", "Kabir Singh"), ("meera", "Meera Iyer"), ("rohan", "Rohan Das"), ("sana", "Sana Khan"), ("vikram", "Vikram Rao"), ("zoya", "Zoya Ali")]
TOPICS = [
    ("Django ORM tricks I wish I knew earlier", "annotate() and Exists() turned a 200-query feed into 7 queries. Profile before you optimise!"),
    ("Template inheritance is underrated", "One base.html, a layout and a few partials. Every page got shorter and consistent."),
    ("Campus hackathon this weekend", "Looking for a frontend person for our team. Ping me if you're interested."),
    ("Best chai near the library?", "Need a study spot that serves decent chai and has working wifi."),
    ("ModelForms save so much time", "Validation, error messages and saving in a handful of lines."),
    ("Finally deployed my first app", "Gunicorn + whitenoise + a cheap VPS. Took two evenings but it works."),
    ("Reading list for the semester", "Two Scoops of Django, Designing Data-Intensive Applications, and the Django docs (seriously)."),
    ("Exam timetable is out", "DBMS on Monday, Full Stack on Wednesday. Good luck everyone."),
    ("Why CSRF tokens matter", "Without them any site could post to your account while you are logged in."),
    ("Weekend trek photos coming soon", "Sunrise at the top was worth the 4am start."),
    ("Dark mode or light mode?", "The eternal debate. I am firmly on the dark side."),
    ("Pagination done right", "Paginator + get_page() handles invalid page numbers for you."),
]
COMMENTS = ["Totally agree!", "This is really helpful, thanks.", "Saving this for later.", "Can you share more details?", "Ha, same here.", "Great point.", "I had the same problem last week."]


class Command(BaseCommand):
    help = "Populate the database with realistic demo data (password for all users: vortex-demo-123)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete existing non-staff users and their content first")

    @transaction.atomic
    def handle(self, *args, flush=False, **options):
        rng = random.Random(42)
        if flush:
            User.objects.filter(is_staff=False).delete()
        users = []
        for username, name in PEOPLE:
            user, created = User.objects.get_or_create(username=username, defaults={"email": f"{username}@vortex.test"})
            if created:
                user.set_password("vortex-demo-123")
                user.save()
            user.profile.full_name = name
            user.profile.bio = f"Hi, I'm {name.split()[0]}. Student, builder, coffee enthusiast."
            user.profile.save()
            users.append(user)
        admin, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@vortex.test", "is_staff": True, "is_superuser": True})
        if created:
            admin.set_password("vortex-admin-123")
            admin.save()

        now = timezone.now()
        posts = []
        for index, (title, content) in enumerate(TOPICS):
            post = Post.objects.create(author=users[index % len(users)], title=title, content=content)
            Post.objects.filter(pk=post.pk).update(created_at=now - timedelta(days=rng.randint(0, 25), hours=rng.randint(0, 23)))
            posts.append(post)

        for follower in users:
            for target in rng.sample(users, 4):
                if target != follower:
                    Follow.objects.get_or_create(follower=follower, following=target)
        for post in posts:
            for user in rng.sample(users, rng.randint(1, 7)):
                Like.objects.get_or_create(user=user, post=post)
            for user in rng.sample(users, rng.randint(0, 3)):
                comment = Comment.objects.create(post=post, author=user, content=rng.choice(COMMENTS))
                if rng.random() < 0.4:
                    Comment.objects.create(post=post, author=post.author, parent=comment, content=f"@{user.username} thanks!")
                if user != post.author:
                    Notification.objects.create(recipient=post.author, actor=user, type="comment", post=post, comment=comment, message=f"{user.username} commented on your post")
            for user in rng.sample(users, rng.randint(0, 2)):
                Bookmark.objects.get_or_create(user=user, post=post)
            if rng.random() < 0.3:
                Repost.objects.get_or_create(user=rng.choice(users), post=post)

        poll = Poll.objects.create(post=posts[10], question="Which theme do you use?")
        options = [poll.options.create(text=text) for text in ("Dark", "Light", "Auto")]
        for user in users:
            PollVote.objects.get_or_create(voter=user, poll=poll, defaults={"option": rng.choice(options)})

        conversation = Conversation.objects.create()
        conversation.participants.add(users[0], users[1])
        for sender, text in [(users[0], "Hey, are you joining the hackathon?"), (users[1], "Yes! Need a frontend person though."), (users[0], "I can do frontend.")]:
            Message.objects.create(conversation=conversation, sender=sender, message=text)

        post_type = ContentType.objects.get_for_model(Post)
        Report.objects.get_or_create(reporter=users[2], content_type=post_type, object_id=posts[3].pk, defaults={"reason": "spam", "details": "Looks like an ad."})
        Report.objects.get_or_create(reporter=users[4], content_type=post_type, object_id=posts[9].pk, defaults={"reason": "other"})
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(users)} users, {len(posts)} posts. Log in as aarav / vortex-demo-123 or admin / vortex-admin-123."))
