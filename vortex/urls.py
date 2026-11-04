from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("core.urls")),
    path("", include("posts.urls")),
    path("", include("interactions.urls")),
    path("", include("messaging.urls")),
    path("", include("notifications.urls")),
    path("", include("moderation.urls")),
    path("", include("reports.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns.append(re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}))
