import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash

from .forms import ProfileForm, RegistrationForm
from .models import Follow


def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return request.POST.dict()


def _user_payload(user):
    profile = getattr(user, "profile", None)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": profile.full_name if profile else "",
        "phone": profile.phone if profile else "",
        "bio": profile.bio if profile else "",
        "avatar_url": profile.avatar.url if profile and profile.avatar else None,
        "allow_mentions": profile.allow_mentions if profile else True,
        "created_at": user.date_joined.isoformat(),
    }


def home(request):
    if request.user.is_authenticated:
        return redirect("feed")
    return render(request, "index.html")


@require_http_methods(["POST"])
def register(request):
    form = RegistrationForm(_json_body(request))
    if not form.is_valid():
        return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
    user = User.objects.create_user(
        username=form.cleaned_data["username"],
        email=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
    )
    login(request, user)
    return JsonResponse({"message": "User created successfully", "user": _user_payload(user)}, status=201)


@require_http_methods(["POST"])
def login_view(request):
    data = _json_body(request)
    identifier = data.get("username") or data.get("email") or ""
    user_record = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
    user = authenticate(request, username=user_record.username if user_record else identifier, password=data.get("password", ""))
    if user is None:
        return JsonResponse({"detail": "Incorrect email or password"}, status=401)
    login(request, user)
    return JsonResponse({"message": "Logged in", "user": _user_payload(user)})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    if request.headers.get("Accept", "").startswith("application/json") or request.method == "POST":
        return JsonResponse({"message": "Logged out"})
    return redirect("home")


@login_required
@require_http_methods(["PUT", "POST"])
def update_profile(request):
    data = _json_body(request)
    profile = request.user.profile
    form = ProfileForm(data, instance=profile)
    if not form.is_valid():
        return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
    if data.get("username") and data["username"] != request.user.username:
        if User.objects.filter(username__iexact=data["username"]).exclude(pk=request.user.pk).exists():
            return JsonResponse({"detail": "Username already taken"}, status=400)
        request.user.username = data["username"]
        request.user.save(update_fields=["username"])
    form.save()
    return JsonResponse(_user_payload(request.user))


@login_required
def me(request):
    if request.method == "DELETE":
        request.user.delete()
        logout(request)
        return JsonResponse({"message": "Account deleted successfully"})
    if request.method in {"PUT", "POST"}:
        return update_profile(request)
    return JsonResponse(_user_payload(request.user))


@login_required
@require_http_methods(["POST"])
def upload_avatar(request):
    form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
    if not form.is_valid():
        return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
    form.save()
    return JsonResponse({"avatar_url": request.user.profile.avatar.url})


@login_required
@require_http_methods(["POST"])
def change_password(request):
    data = _json_body(request)
    if not request.user.check_password(data.get("current_password", "")):
        return JsonResponse({"detail": "Current password is incorrect"}, status=400)
    new_password = data.get("new_password", "")
    if len(new_password) < 8:
        return JsonResponse({"detail": "New password must be at least 8 characters"}, status=400)
    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)
    return JsonResponse({"message": "Password changed successfully"})


@login_required
def public_profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    data = _user_payload(user)
    data["followers_count"] = Follow.objects.filter(following=user).count()
    data["following_count"] = Follow.objects.filter(follower=user).count()
    data["is_following"] = Follow.objects.filter(follower=request.user, following=user).exists()
    return JsonResponse(data)


def search_users(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    users = User.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)).select_related("profile")[:15]
    return JsonResponse([_user_payload(user) for user in users], safe=False)


@login_required
def mentionable_users(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.filter(profile__allow_mentions=True).exclude(pk=request.user.pk)
    if query:
        users = users.filter(username__icontains=query)
    return JsonResponse([_user_payload(user) for user in users.order_by("username")[:15]], safe=False)
