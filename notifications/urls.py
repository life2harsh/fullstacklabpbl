from django.urls import path

from . import views

urlpatterns = [
    path("notifications-page/", views.notifications_page, name="notifications-page"),
    path("notifications", views.notifications, name="notifications"),
    path("notifications/read-all", views.mark_all_read, name="mark-all-read"),
    path("notifications/<int:notification_id>/read", views.mark_read, name="mark-read"),
]
