from django import template

register = template.Library()


@register.inclusion_tag("partials/_avatar.html")
def avatar(user, size=""):
    profile = getattr(user, "profile", None)
    return {"user": user, "url": profile.avatar.url if profile and profile.avatar else None, "size": size}
