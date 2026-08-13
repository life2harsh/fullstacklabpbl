import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import ModerationFilterForm, ReportForm
from .models import Report


def _payload(report):
    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "report_type": report.report_type,
        "target_id": report.target_id,
        "reason": report.reason,
        "details": report.details,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
    }


def _body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return request.POST.dict()


@login_required
@require_http_methods(["POST"])
def create_report(request):
    form = ReportForm(_body(request))
    if not form.is_valid():
        return JsonResponse({"detail": form.errors.get_json_data()}, status=400)
    report = form.save(commit=False)
    report.reporter = request.user
    report.save()
    return JsonResponse(_payload(report), status=201)


@login_required
@user_passes_test(lambda user: user.is_staff)
def reports_list(request):
    form = ModerationFilterForm(request.GET)
    reports = Report.objects.select_related("reporter")
    if form.is_valid() and form.cleaned_data.get("status"):
        reports = reports.filter(status=form.cleaned_data["status"])
    return JsonResponse([_payload(report) for report in reports], safe=False)


@login_required
@user_passes_test(lambda user: user.is_staff)
def moderation_page(request):
    return render(request, "moderation.html", {"reports": Report.objects.select_related("reporter")[:50]})
