from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Count, Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.utils import avatar_url
from moderation.forms import ReportForm
from posts.models import Post

from .forms import LoginForm, ProfileForm, RegistrationForm, UserForm
from .models import Block, Follow


def _user_payload(user, private=False):
    data = {
        "id": user.id,
        "username": user.username,
        "full_name": user.profile.full_name,
        "bio": user.profile.bio,
        "avatar_url": avatar_url(user),
        "created_at": user.date_joined.isoformat(),
    }
    if private:
        data.update(email=user.email, phone=user.profile.phone, allow_mentions=user.profile.allow_mentions)
    return data


def _auth_page(request, login_form=None, signup_form=None, tab="login"):
    return render(request, "index.html", {
        "login_form": login_form or LoginForm(request),
        "signup_form": signup_form or RegistrationForm(),
        "tab": tab,
    }, status=400 if request.method == "POST" else 200)


def home(request):
    if request.user.is_authenticated:
        return redirect("feed")
    return _auth_page(request)


@require_POST
def login_view(request):
    form = LoginForm(request, data=request.POST)
    if not form.is_valid():
        return _auth_page(request, login_form=form)
    login(request, form.get_user())
    return redirect(request.POST.get("next") or "feed")


@require_POST
def register(request):
    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return _auth_page(request, signup_form=form, tab="signup")
    login(request, form.save())
    messages.success(request, "Welcome to Vortex!")
    return redirect("feed")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def profile_page(request):
    user_form = UserForm(instance=request.user)
    profile_form = ProfileForm(instance=request.user.profile)
    password_form = PasswordChangeForm(request.user)
    if request.method == "POST" and request.POST.get("form") == "password":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            update_session_auth_hash(request, password_form.save())
            messages.success(request, "Password changed.")
            return redirect("profile-page")
    elif request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile-page")
    return render(request, "profile.html", {
        "profile_user": request.user,
        "posts": Post.objects.filter(author=request.user).with_stats(request.user),
        "user_form": user_form,
        "profile_form": profile_form,
        "password_form": password_form,
        "editing": request.method == "POST",
        **_follow_lists(request.user),
    })


@login_required
@require_POST
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()
    messages.success(request, "Your account has been deleted.")
    return redirect("home")


def _follow_lists(user):
    return {
        "followers": User.objects.filter(following_links__following=user).select_related("profile"),
        "following": User.objects.filter(follower_links__follower=user).select_related("profile"),
    }


@login_required
def public_profile_page(request, user_id):
    if user_id == request.user.id:
        return redirect("profile-page")
    profile_user = get_object_or_404(User.objects.select_related("profile").annotate(
        is_following=Exists(Follow.objects.filter(follower=request.user, following=OuterRef("pk"))),
        is_blocked=Exists(Block.objects.filter(blocker=request.user, blocked=OuterRef("pk"))),
        post_total=Count("posts", distinct=True),
    ), pk=user_id, is_active=True)
    return render(request, "public-profile.html", {
        "profile_user": profile_user,
        "posts": Post.objects.filter(author=profile_user).visible_to(request.user).with_stats(request.user),
        "report_form": ReportForm(),
        **_follow_lists(profile_user),
    })


@login_required
def me(request):
    return JsonResponse(_user_payload(request.user, private=True))


@login_required
def user_detail(request, user_id):
    return JsonResponse(_user_payload(get_object_or_404(User.objects.select_related("profile"), pk=user_id, is_active=True)))


@login_required
def mentionable_users(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.filter(profile__allow_mentions=True, is_active=True, username__icontains=query).exclude(pk=request.user.pk).select_related("profile")
    return JsonResponse([_user_payload(user) for user in users.order_by("username")[:15]], safe=False)
