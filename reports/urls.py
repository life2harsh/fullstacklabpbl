from django.urls import path

from . import views

urlpatterns = [
    path("reports/activity/", views.activity_page, name="activity-report"),
    path("reports/activity.csv", views.export_csv, name="activity-csv"),
    path("reports/activity.pdf", views.export_pdf, name="activity-pdf"),
    path("reports/analytics/", views.analytics_page, name="analytics"),
    path("reports/analytics.csv", views.analytics_csv, name="analytics-csv"),
    path("reports/analytics.pdf", views.analytics_pdf, name="analytics-pdf"),
]
