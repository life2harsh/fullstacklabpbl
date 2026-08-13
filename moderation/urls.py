from django.urls import path

from . import views

urlpatterns = [
    path("reports", views.create_report, name="create-report"),
    path("reports/all", views.reports_list, name="reports-list"),
    path("moderation/", views.moderation_page, name="moderation-page"),
]
