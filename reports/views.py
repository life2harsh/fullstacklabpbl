import csv
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from posts.models import Post

from .forms import ActivityReportForm


@login_required
def activity_page(request):
    return render(request, "activity-report.html", {"form": ActivityReportForm()})


@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="vortex-activity.csv"'
    writer = csv.writer(response)
    writer.writerow(["Post ID", "Title", "Content", "Created At", "Likes", "Comments", "Reposts"])
    posts = Post.objects.filter(author=request.user).prefetch_related("likes", "comments", "reposts")
    for post in posts:
        writer.writerow([post.id, post.title, post.content, post.created_at.isoformat(), post.likes.count(), post.comments.count(), post.reposts.count()])
    return response


@login_required
def export_pdf(request):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Vortex User Activity Report")
    y = 760
    profile = request.user.profile
    posts = Post.objects.filter(author=request.user).prefetch_related("likes", "comments", "reposts")
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
