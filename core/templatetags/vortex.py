from django import template
from django.urls import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from posts.models import HASHTAG

register = template.Library()


@register.inclusion_tag("partials/_avatar.html")
def avatar(user, size=""):
    profile = getattr(user, "profile", None)
    return {"user": user, "url": profile.avatar.url if profile and profile.avatar else None, "size": size}


@register.filter
def hashtags(text):
    feed = reverse("feed")
    return mark_safe(HASHTAG.sub(lambda match: f'<a class="hashtag" href="{feed}?tag={match[1].lower()}">#{match[1]}</a>', conditional_escape(text)))
