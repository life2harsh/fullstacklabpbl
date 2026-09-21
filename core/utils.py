import json


def json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return request.POST.dict()


def avatar_url(user):
    profile = getattr(user, "profile", None)
    return profile.avatar.url if profile and profile.avatar else None


def is_ajax(request):
    return request.headers.get("X-Requested-With") == "fetch"
