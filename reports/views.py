from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, F, Q
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from interactions.models import Like
from moderation.models import Report
from posts.models import Comment, Post

from .exports import csv_response, pdf_response
from .forms import ActivityReportForm, DateRangeForm


def _activity(request):
    form = ActivityReportForm(request.GET or None)
    days, include_comments = (form.cleaned_data["days"], form.cleaned_data["include_comments"]) if form.is_valid() else (30, True)
    posts = Post.objects.filter(author=request.user, created_at__gte=timezone.now() - timedelta(days=days)).with_stats(request.user).annotate(
        score=F("like_count") + 2 * F("comment_count") + 3 * F("repost_count")
    ).order_by("-score", "-created_at")
    return form, days, include_comments, posts


def _activity_rows(posts, include_comments):
    headers = ["Post ID", "Title", "Created", "Likes", *(["Comments"] if include_comments else []), "Reposts", "Engagement"]
    rows = [[p.id, p.title, f"{p.created_at:%Y-%m-%d}", p.like_count, *([p.comment_count] if include_comments else []), p.repost_count, p.score] for p in posts]
    return headers, rows


@login_required
def activity_page(request):
    form, days, include_comments, posts = _activity(request)
    return render(request, "activity-report.html", {"form": form, "days": days, "posts": posts[:10], "include_comments": include_comments, "query": request.GET.urlencode()})


@login_required
def export_csv(request):
    _, _, include_comments, posts = _activity(request)
    headers, rows = _activity_rows(posts, include_comments)
    return csv_response("vortex-activity.csv", headers, rows)


@login_required
def export_pdf(request):
    _, days, include_comments, posts = _activity(request)
    user, profile = request.user, request.user.profile
    headers, rows = _activity_rows(posts, include_comments)
    totals = [["Posts", "Likes received", "Comments received", "Reposts received", "Followers", "Following"], [
        len(rows), sum(p.like_count for p in posts), sum(p.comment_count for p in posts), sum(p.repost_count for p in posts),
        user.follower_links.count(), user.following_links.count(),
    ]]
    return pdf_response("vortex-activity-report.pdf", "Vortex Activity Report", [
        ("p", f"<b>{user.username}</b> · {profile.full_name or 'No name set'} · member since {user.date_joined:%d %b %Y}"),
        ("p", f"Reporting window: last {days} days (generated {timezone.localtime():%d %b %Y %H:%M})"),
        ("h", "Summary"), ("table", totals),
        ("h", "Posts by engagement"), ("table", [headers, *rows]),
    ])


def _analytics(request):
    form = DateRangeForm(request.GET)
    start, end = form.range()
    window = Q(created_at__date__gte=start, created_at__date__lte=end)
    posts = Post.objects.filter(window)
    daily = list(posts.annotate(day=TruncDate("created_at")).values("day").annotate(posts=Count("id")).order_by("day"))
    comments_by_day = dict(Comment.objects.filter(window).annotate(day=TruncDate("created_at")).values("day").annotate(n=Count("id")).values_list("day", "n"))
    for row in daily:
        row["comments"] = comments_by_day.get(row["day"], 0)
    author_window = Q(posts__created_at__date__gte=start, posts__created_at__date__lte=end)
    return {
        "form": form,
        "start": start,
        "end": end,
        "totals": {
            "New users": User.objects.filter(date_joined__date__gte=start, date_joined__date__lte=end).count(),
            "Posts": posts.count(),
            "Comments": Comment.objects.filter(window).count(),
            "Likes": Like.objects.filter(window).count(),
            "Open reports": Report.objects.filter(status="pending").count(),
        },
        "daily": daily,
        "peak": max((row["posts"] for row in daily), default=0),
        "top_authors": User.objects.annotate(post_total=Count("posts", filter=author_window, distinct=True), like_total=Count("posts__likes", filter=author_window, distinct=True)).filter(post_total__gt=0).order_by("-like_total", "-post_total")[:10],
        "top_posts": posts.with_stats().annotate(score=F("like_count") + 2 * F("comment_count") + 3 * F("repost_count")).order_by("-score")[:10],
        "report_reasons": Report.objects.filter(window).values("reason").annotate(n=Count("id")).order_by("-n"),
    }


@staff_member_required
def analytics_page(request):
    return render(request, "analytics.html", {**_analytics(request), "query": request.GET.urlencode()})


@staff_member_required
def analytics_csv(request):
    data = _analytics(request)
    return csv_response(f"vortex-analytics-{data['start']}-{data['end']}.csv", ["Date", "Posts", "Comments"], ([row["day"], row["posts"], row["comments"]] for row in data["daily"]))


@staff_member_required
def analytics_pdf(request):
    data = _analytics(request)
    return pdf_response("vortex-analytics.pdf", "Vortex Platform Analytics", [
        ("p", f"Period: {data['start']:%d %b %Y} – {data['end']:%d %b %Y}"),
        ("h", "Totals"), ("table", [list(data["totals"]), list(data["totals"].values())]),
        ("h", "Daily activity"), ("table", [["Date", "Posts", "Comments"], *([f"{r['day']:%Y-%m-%d}", r["posts"], r["comments"]] for r in data["daily"])]),
        ("h", "Top authors"), ("table", [["Author", "Posts", "Likes"], *([u.username, u.post_total, u.like_total] for u in data["top_authors"])]),
        ("h", "Top posts"), ("table", [["Title", "Author", "Likes", "Comments", "Score"], *([p.title[:50], p.author.username, p.like_count, p.comment_count, p.score] for p in data["top_posts"])]),
    ])
