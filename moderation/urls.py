from django.urls import path

from . import views

urlpatterns = [
    path("report/<str:kind>/<int:object_id>/", views.report_target, name="report-target"),
    path("moderation/", views.moderation_page, name="moderation-page"),
    path("moderation/<int:report_id>/<str:action>/", views.moderate, name="moderate"),
]
