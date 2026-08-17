import json

from django.contrib.auth.models import User
from django.test import Client, TestCase

from accounts.models import Follow
from interactions.models import Like
from messaging.models import Conversation, ConversationParticipant
from posts.models import Comment, Post


class VortexWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="strong-pass-123")
        self.other = User.objects.create_user(username="bob", email="bob@example.com", password="strong-pass-123")

    def login(self, user=None):
        user = user or self.user
        response = self.client.post("/login", {"username": user.email, "password": "strong-pass-123"})
        self.assertEqual(response.status_code, 200)

    def test_registration_and_session_login(self):
        response = self.client.post("/signup", data=json.dumps({"username": "new-user", "email": "new@example.com", "password": "strong-pass-123"}), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_registration_works_with_django_csrf_protection(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.get("/")
        csrf_token = csrf_client.cookies["csrftoken"].value
        response = csrf_client.post(
            "/signup",
            data=json.dumps({"username": "csrf-user", "email": "csrf@example.com", "password": "strong-pass-123"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 201)

    def test_protected_route_and_post_crud_permissions(self):
        self.assertEqual(self.client.get("/posts").status_code, 302)
        self.login()
        response = self.client.post("/posts", {"title": "First post", "content": "A useful Django post"})
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(title="First post")
        self.assertEqual(post.author, self.user)

        self.client.logout()
        self.login(self.other)
        response = self.client.put(f"/posts/{post.id}", data=json.dumps({"title": "Hijacked"}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.login()
        response = self.client.put(f"/posts/{post.id}", data=json.dumps({"title": "Edited"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(f"/posts/{post.id}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(pk=post.id).exists())

    def test_comments_like_follow_and_search_ajax(self):
        self.login()
        post = Post.objects.create(author=self.user, title="Django ORM", content="Searchable content")
        comment_response = self.client.post(f"/posts/{post.id}/comments", {"content": "Nice post"})
        self.assertEqual(comment_response.status_code, 201)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(self.client.post(f"/posts/{post.id}/like").status_code, 200)
        self.assertTrue(Like.objects.filter(user=self.user, post=post).exists())
        self.assertEqual(self.client.post(f"/users/{self.other.id}/follow").status_code, 200)
        self.assertTrue(Follow.objects.filter(follower=self.user, following=self.other).exists())
        search_response = self.client.get("/search/?q=searchable")
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(len(search_response.json()["posts"]), 1)

    def test_reports_and_relationships(self):
        self.login()
        post = Post.objects.create(author=self.user, title="Report me", content="Exportable")
        self.assertEqual(self.client.get("/reports/activity.csv").status_code, 200)
        self.assertIn("text/csv", self.client.get("/reports/activity.csv")["Content-Type"])
        pdf = self.client.get("/reports/activity.pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        conversation = Conversation.objects.create()
        ConversationParticipant.objects.create(conversation=conversation, user=self.user)
        ConversationParticipant.objects.create(conversation=conversation, user=self.other)
        self.assertEqual(conversation.participants.count(), 2)
