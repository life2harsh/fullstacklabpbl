import csv
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from posts.models import Post

from .forms import ActivityReportForm


def _report_options(request):
    form = ActivityReportForm(request.GET or None)
    if form.is_valid():
        days = form.cleaned_data["days"]
        include_comments = form.cleaned_data["include_comments"]
    else:
        days = 30
        include_comments = True
    since = timezone.now() - timedelta(days=days)
    return form, since, include_comments


@login_required
def activity_page(request):
    form, _, _ = _report_options(request)
    return render(request, "activity-report.html", {"form": form})


@login_required
def export_csv(request):
    _, since, include_comments = _report_options(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="vortex-activity.csv"'
    writer = csv.writer(response)
    headers = ["Post ID", "Title", "Content", "Created At", "Likes"]
    if include_comments:
        headers.append("Comments")
    headers.append("Reposts")
    writer.writerow(headers)
    posts = Post.objects.filter(author=request.user, created_at__gte=since).prefetch_related("likes", "comments", "reposts")
    for post in posts:
        row = [post.id, post.title, post.content, post.created_at.isoformat(), post.likes.count()]
        if include_comments:
            row.append(post.comments.count())
        row.append(post.reposts.count())
        writer.writerow(row)
    return response


@login_required
def export_pdf(request):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    _, since, include_comments = _report_options(request)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Vortex User Activity Report")
    y = 760
    profile = request.user.profile
    posts = Post.objects.filter(author=request.user, created_at__gte=since).prefetch_related("likes", "comments", "reposts")
    lines = [
        "Vortex User Activity Report",
        f"Username: {request.user.username}",
        f"Name: {profile.full_name or 'Not provided'}",
        f"Account created: {request.user.date_joined:%Y-%m-%d}",
        f"Total posts: {posts.count()}",
        f"Followers: {request.user.follower_links.count()}   Following: {request.user.following_links.count()}",
        f"Likes received: {sum(post.likes.count() for post in posts)}",
        f"Reposts received: {sum(post.reposts.count() for post in posts)}",
        "",
        "Top posts:",
    ]
    if include_comments:
        lines.insert(7, f"Comments received: {sum(post.comments.count() for post in posts)}")
    for post in posts:
        score = post.likes.count() + post.comments.count() * 2 + post.reposts.count() * 3
        lines.append(f"- {post.title[:65]} ({score} engagement)")
    for line in lines:
        pdf.drawString(50, y, line[:110])
        y -= 18
        if y < 50:
            pdf.showPage()
            y = 760
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="vortex-activity-report.pdf"'
    return response
