from datetime import timedelta

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Block, Follow
from interactions.models import Like
from moderation.models import Report
from notifications.models import Notification
from posts.models import Comment, Poll, PollVote, Post, Tag
from vortex.asgi import application

PASSWORD = "strong-pass-123"


class VortexTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password=PASSWORD)
        self.other = User.objects.create_user(username="bob", email="bob@example.com", password=PASSWORD)

    def login(self, user=None):
        response = self.client.post("/login", {"username": (user or self.user).email, "password": PASSWORD})
        self.assertRedirects(response, "/feed/")


class AuthTests(VortexTestCase):
    def test_signup_logs_in_and_stores_profile(self):
        response = self.client.post("/signup", {"username": "new_user", "email": "new@example.com", "full_name": "New User", "password": PASSWORD})
        self.assertRedirects(response, "/feed/")
        self.assertEqual(User.objects.get(username="new_user").profile.full_name, "New User")

    def test_signup_shows_form_errors(self):
        response = self.client.post("/signup", {"username": "alice", "email": "x@example.com", "password": "short"})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Username already taken.", status_code=400)

    def test_login_with_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/")
        response = client.post("/login", {"username": "alice", "password": PASSWORD, "csrfmiddlewaretoken": client.cookies["csrftoken"].value})
        self.assertRedirects(response, "/feed/")

    def test_deactivated_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post("/login", {"username": "alice", "password": PASSWORD})
        self.assertEqual(response.status_code, 400)

    def test_logout_and_protected_routes(self):
        self.login()
        self.client.post("/logout")
        for url in ["/feed/", "/profile/", "/notifications/", "/chat/", "/reports/activity/"]:
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_user_json_does_not_leak_private_fields(self):
        self.login()
        public = self.client.get(f"/users/{self.other.id}").json()
        self.assertNotIn("email", public)
        self.assertNotIn("phone", public)
        self.assertEqual(self.client.get("/users/me").json()["email"], "alice@example.com")

    def test_profile_update_and_password_change(self):
        self.login()
        response = self.client.post("/profile/", {"form": "profile", "username": "alice2", "email": "alice@example.com", "full_name": "Alice", "bio": "hi", "allow_mentions": "on"})
        self.assertRedirects(response, "/profile/")
        self.assertEqual(User.objects.get(pk=self.user.pk).username, "alice2")
        response = self.client.post("/profile/", {"form": "password", "old_password": PASSWORD, "new_password1": "another-pass-456", "new_password2": "another-pass-456"})
        self.assertRedirects(response, "/profile/")
        self.assertTrue(User.objects.get(pk=self.user.pk).check_password("another-pass-456"))

    def test_password_reset_by_email(self):
        self.assertRedirects(self.client.post("/password-reset/", {"email": "alice@example.com"}), "/password-reset/sent/")
        self.assertEqual(len(mail.outbox), 1)
        link = next(line for line in mail.outbox[0].body.splitlines() if "/reset/" in line).strip()
        form_url = self.client.get(link).url
        response = self.client.post(form_url, {"new_password1": "reset-pass-789", "new_password2": "reset-pass-789"})
        self.assertRedirects(response, "/reset/done/")
        self.assertTrue(User.objects.get(pk=self.user.pk).check_password("reset-pass-789"))
        self.assertContains(self.client.get(link), "invalid")


class PostTests(VortexTestCase):
    def test_create_post_with_poll_formset(self):
        self.login()
        response = self.client.post("/feed/", {
            "title": "Lunch?", "content": "Vote @bob",
            "poll-question": "Where?",
            "option-TOTAL_FORMS": 4, "option-INITIAL_FORMS": 0, "option-MIN_NUM_FORMS": 0, "option-MAX_NUM_FORMS": 6,
            "option-0-text": "Pizza", "option-1-text": "Tacos", "option-2-text": "", "option-3-text": "",
        })
        post = Post.objects.get(title="Lunch?")
        self.assertRedirects(response, post.get_absolute_url())
        self.assertEqual(post.poll.options.count(), 2)
        self.assertTrue(Notification.objects.filter(recipient=self.other, type="mention").exists())

    def test_poll_requires_two_options(self):
        self.login()
        response = self.client.post("/feed/", {
            "title": "Bad poll", "content": "x", "poll-question": "Only one?",
            "option-TOTAL_FORMS": 1, "option-INITIAL_FORMS": 0, "option-MIN_NUM_FORMS": 0, "option-MAX_NUM_FORMS": 6, "option-0-text": "Yes",
        })
        self.assertContains(response, "at least two options")
        self.assertFalse(Post.objects.exists())

    def test_one_vote_per_poll(self):
        self.login()
        post = Post.objects.create(author=self.other, title="Q", content="c")
        poll = Poll.objects.create(post=post, question="?")
        a, b = poll.options.create(text="A"), poll.options.create(text="B")
        self.client.post(reverse("vote-poll", args=[poll.pk]), {"option": a.pk})
        self.client.post(reverse("vote-poll", args=[poll.pk]), {"option": b.pk})
        self.assertEqual(list(PollVote.objects.values_list("option", flat=True)), [b.pk])

    def test_edit_and_delete_permissions(self):
        post = Post.objects.create(author=self.user, title="Mine", content="c")
        self.login(self.other)
        self.assertEqual(self.client.post(reverse("post-edit", args=[post.pk]), {"title": "Hijack", "content": "x"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("post-delete", args=[post.pk])).status_code, 403)
        self.client.post("/logout")
        self.login()
        self.client.post(reverse("post-edit", args=[post.pk]), {"title": "Edited", "content": "c"})
        self.assertEqual(Post.objects.get(pk=post.pk).title, "Edited")
        self.assertRedirects(self.client.post(reverse("post-delete", args=[post.pk])), "/feed/")
        self.assertFalse(Post.objects.exists())

    def test_threaded_comments_and_notifications(self):
        post = Post.objects.create(author=self.other, title="Thread", content="c")
        self.login()
        self.client.post(post.get_absolute_url(), {"content": "Top level"})
        parent = Comment.objects.get()
        self.client.post("/logout")
        self.login(self.other)
        self.client.post(post.get_absolute_url(), {"content": "Reply", "parent": parent.pk})
        self.assertEqual(parent.replies.count(), 1)
        self.assertTrue(Notification.objects.filter(recipient=self.user, message__contains="replied").exists())
        self.assertContains(self.client.get(post.get_absolute_url()), "Reply")

    def test_feed_query_count_is_constant(self):
        for i in range(15):
            post = Post.objects.create(author=self.other, title=f"Post {i}", content="body")
            Like.objects.create(user=self.user, post=post)
        self.login()
        with self.assertNumQueries(8):
            self.client.get("/feed/")

    def test_live_search_returns_partial(self):
        Post.objects.create(author=self.other, title="Django ORM tips", content="Searchable")
        self.login()
        response = self.client.get("/feed/?q=searchable", HTTP_X_REQUESTED_WITH="fetch")
        self.assertContains(response, "Django ORM tips")
        self.assertNotContains(response, "<html")

    def test_hashtags_link_filter_and_trend(self):
        post = Post.objects.create(author=self.user, title="Shipping", content="Deployed it #Django #deploy")
        post.sync_tags()
        Post.objects.create(author=self.user, title="Untagged", content="nothing here")
        self.login()
        self.assertEqual(set(post.tags.values_list("name", flat=True)), {"django", "deploy"})
        response = self.client.get("/feed/?tag=django")
        self.assertContains(response, "Shipping")
        self.assertNotContains(response, "Untagged")
        self.assertContains(response, 'href="/feed/?tag=django"')
        self.assertEqual([tag.name for tag in Tag.trending()], ["deploy", "django"])
        self.client.post(reverse("post-edit", args=[post.pk]), {"title": "Shipping", "content": "Now only #deploy"})
        self.assertEqual(list(post.tags.values_list("name", flat=True)), ["deploy"])

    def test_blocked_authors_hidden(self):
        Post.objects.create(author=self.other, title="Hidden post", content="c")
        Block.objects.create(blocker=self.user, blocked=self.other)
        self.login()
        self.assertNotContains(self.client.get("/feed/"), "Hidden post")


class InteractionTests(VortexTestCase):
    def test_like_toggle_returns_count(self):
        post = Post.objects.create(author=self.other, title="T", content="c")
        self.login()
        self.assertEqual(self.client.post(f"/posts/{post.id}/like").json(), {"active": True, "count": 1})
        self.assertEqual(self.client.post(f"/posts/{post.id}/like").json(), {"active": False, "count": 0})
        self.assertEqual(Notification.objects.filter(type="like").count(), 1)

    def test_follow_and_block(self):
        self.login()
        self.assertTrue(self.client.post(f"/users/{self.other.id}/follow").json()["active"])
        self.assertTrue(Follow.objects.exists())
        self.assertTrue(self.client.post(f"/users/{self.other.id}/block").json()["active"])
        self.assertFalse(Follow.objects.exists())
        self.assertEqual(self.client.post(f"/users/{self.other.id}/follow").status_code, 400)


class ModerationTests(VortexTestCase):
    def test_report_and_remove_content(self):
        post = Post.objects.create(author=self.other, title="Spam", content="buy now")
        self.login()
        self.client.post(reverse("report-target", args=["post", post.pk]), {"reason": "spam"})
        report = Report.objects.get()
        self.assertEqual(report.target, post)
        self.assertEqual(self.client.get("/moderation/").status_code, 302)
        self.user.is_staff = True
        self.user.save()
        self.assertContains(self.client.get("/moderation/"), "buy now")
        self.client.post(reverse("moderate", args=[report.pk, "remove"]))
        self.assertFalse(Post.objects.exists())
        self.assertEqual(Report.objects.get().status, "removed")

    def test_reporting_user_deactivates_on_remove(self):
        report = Report.objects.create(reporter=self.user, content_type=ContentType.objects.get_for_model(User), object_id=self.other.pk, reason="harassment")
        report.resolve("remove")
        self.other.refresh_from_db()
        self.assertFalse(self.other.is_active)


class ReportExportTests(VortexTestCase):
    def test_activity_csv_and_pdf(self):
        Post.objects.create(author=self.user, title="Recent report", content="Exportable")
        old = Post.objects.create(author=self.user, title="Old report", content="Outside range")
        Post.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=60))
        self.login()
        csv_text = self.client.get("/reports/activity.csv?days=30&include_comments=on").content.decode()
        self.assertIn("Recent report", csv_text)
        self.assertNotIn("Old report", csv_text)
        self.assertIn("Comments", csv_text.splitlines()[0])
        self.assertNotIn("Comments", self.client.get("/reports/activity.csv?days=30").content.decode().splitlines()[0])
        pdf = self.client.get("/reports/activity.pdf")
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_analytics_is_staff_only(self):
        Post.objects.create(author=self.other, title="Counted", content="c")
        self.login()
        self.assertEqual(self.client.get("/reports/analytics/").status_code, 302)
        self.user.is_staff = True
        self.user.save()
        self.assertContains(self.client.get("/reports/analytics/"), "Counted")
        self.assertIn("Posts", self.client.get("/reports/analytics.csv").content.decode())
        self.assertTrue(self.client.get("/reports/analytics.pdf").content.startswith(b"%PDF"))
        bad = self.client.get("/reports/analytics/?start=2026-02-01&end=2026-01-01")
        self.assertContains(bad, "Start date must be on or before")


class RealtimeChatTests(VortexTestCase):
    async def socket_for(self, user):
        client = Client()
        await sync_to_async(client.force_login)(user)
        communicator = WebsocketCommunicator(application, "/ws/chat/", headers=[
            (b"cookie", f"sessionid={client.cookies['sessionid'].value}".encode()), (b"origin", b"http://testserver")])
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def test_message_and_typing_are_pushed(self):
        bob = await self.socket_for(self.other)
        alice = await self.socket_for(self.user)
        await sync_to_async(self.client.force_login)(self.user)
        await sync_to_async(self.client.post)("/messages", {"receiver_id": self.other.id, "message": "hi bob"})
        event = await bob.receive_json_from(timeout=2)
        self.assertEqual((event["event"], event["sender_id"], event["preview"]), ("message", self.user.id, "hi bob"))
        self.assertEqual((await alice.receive_json_from(timeout=2))["event"], "message")
        await alice.send_json_to({"typing": self.other.id})
        self.assertEqual(await bob.receive_json_from(timeout=2), {"event": "typing", "user": self.user.id})
        await alice.disconnect()
        await bob.disconnect()

    async def test_anonymous_socket_is_rejected(self):
        communicator = WebsocketCommunicator(application, "/ws/chat/", headers=[(b"origin", b"http://testserver")])
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
