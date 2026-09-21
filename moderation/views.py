from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from posts.models import Comment, Post

from .forms import ModerationFilterForm, ReportForm
from .models import Report

TARGETS = {"post": Post, "comment": Comment, "user": User}
ACTIONS = {"review": "Mark reviewed", "dismiss": "Dismiss", "remove": "Remove content"}


@login_required
@require_POST
def report_target(request, kind, object_id):
    model = TARGETS.get(kind)
    if model is None:
        return redirect("feed")
    target = get_object_or_404(model, pk=object_id)
    form = ReportForm(request.POST)
    content_type = ContentType.objects.get_for_model(model)
    if Report.objects.filter(reporter=request.user, content_type=content_type, object_id=target.pk).exists():
        messages.info(request, "You have already reported this.")
    elif form.is_valid():
        form.instance.reporter = request.user
        form.instance.content_type = content_type
        form.instance.object_id = target.pk
        form.save()
        messages.success(request, "Thanks — a moderator will review your report.")
    else:
        messages.error(request, "Pick a reason for the report.")
    return redirect(request.POST.get("next") or "feed")


@staff_member_required
def moderation_page(request):
    form = ModerationFilterForm(request.GET or None)
    reports = Report.objects.select_related("reporter", "content_type").prefetch_related("target")
    if form.is_valid():
        if form.cleaned_data["status"]:
            reports = reports.filter(status=form.cleaned_data["status"])
        if form.cleaned_data["kind"]:
            reports = reports.filter(content_type__model=form.cleaned_data["kind"])
    return render(request, "moderation.html", {"form": form, "reports": reports[:100], "actions": ACTIONS.items()})


@staff_member_required
@require_POST
def moderate(request, report_id, action):
    report = get_object_or_404(Report, pk=report_id)
    if action in ACTIONS:
        report.resolve(action)
        messages.success(request, f"Report #{report.pk}: {action} applied.")
    return redirect(request.POST.get("next") or "moderation-page")
