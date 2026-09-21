from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.notifications_page, name="notifications-page"),
    path("notifications/<int:notification_id>/open/", views.open_notification, name="open-notification"),
    path("notifications/read-all/", views.mark_all_read, name="mark-all-read"),
]
