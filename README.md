# Vortex — Django Full-Stack Social Network

![CI](https://github.com/life2harsh/fullstacklabpbl/actions/workflows/ci.yml/badge.svg)

Vortex is a course-ready Python/Django social network for sharing posts, discussing ideas, following people, messaging, and reviewing community reports. The migration keeps the original noir visual identity and vanilla JavaScript interactions while replacing the FastAPI/SQLAlchemy backend with Django MVT, Django ORM, session authentication, templates, forms, admin, and report exports.

## Problem statement

Small communities need one place to publish updates, discover people, have conversations, and manage harmful or unwanted content. Vortex demonstrates that workflow as a multi-page full-stack web application rather than a collection of disconnected demos.

## Features

- Registration, login (email or username), logout, password change, password reset by email and account deletion using Django forms, `AuthenticationForm`, `PasswordChangeForm`, Django's reset views and session auth
- Server-rendered feed with Latest / Following / Trending / Bookmarks tabs, pagination and live (debounced AJAX) search over posts and people
- Post CRUD with image uploads, optional polls built with an inline formset, threaded comment replies, `@mentions`, `#hashtags` (many-to-many `Tag`) with tag filtering and a trending-tags strip
- AJAX likes, reposts, bookmarks, follows and blocks that return JSON and update counts in place
- Real-time chat over WebSockets (Django Channels): new messages, edits and typing indicators are pushed instantly, with polling as a fallback when the socket drops
- Notifications with unread badges supplied by a context processor
- Report button on posts, comments and users; a staff moderation queue to review, dismiss or remove content; matching Django Admin actions
- Personal activity report and staff platform analytics (date-range form, aggregate QuerySets), both exportable as CSV and PDF
- Customised Django Admin: inlines, annotated list columns, filters, date hierarchy and CSV export actions
- `manage.py seed` command for realistic demo data

## Technology stack

Python 3.11+ · Django 5.2 · Django ORM · SQLite for local development · MySQL through `DATABASE_URL` · vanilla HTML/CSS/JavaScript · PyMySQL · Pillow · ReportLab · Channels + Daphne (ASGI) · WhiteNoise · GitHub Actions

## Architecture

```text
vortex/
├── manage.py
├── vortex/                 # settings, root URLs, WSGI, ASGI router (HTTP + WebSocket)
├── accounts/               # registration, sessions, Profile, follows, blocks
├── posts/                  # Post, Comment, Poll, Mention, CRUD and search
├── interactions/           # likes, reposts, bookmarks, follows/block actions
├── messaging/              # Conversation, participants, Message CRUD, ChatConsumer
├── notifications/          # notification feed and read state
├── moderation/             # user-submitted reports and staff queue
├── reports/                # activity + analytics pages, CSV/PDF exports
├── core/                   # shared helpers, badge context processor, {% avatar %} tag, seed command
├── templates/              # inherited Django templates
├── static/                 # original Vortex styles plus AJAX helper
└── media/                  # local uploads, ignored by git
```

Pages are rendered with function-based views and the Django Template Language. `base.html` → `layout.html` (sidebar) → page templates, with reusable partials in `templates/partials/` (post card, comment thread, poll, report form, form fields). JavaScript is limited to progressive enhancement in `static/js/app.js`: CSRF-aware fetch, toggle buttons, live search and badge polling. Chat is the only page rendered on the client. It sends messages over HTTP (so uploads and CSRF work as usual); the view then pushes an event through the channel layer to each participant's `user-<id>` group, and the open `ChatConsumer` forwards it to the browser.

`Post.objects.with_stats(user)` annotates like, comment and repost counts plus `is_liked`/`is_bookmarked`/`is_reposted` flags (`Count` + `Exists` subqueries), so the feed always takes 7 queries regardless of how many posts it shows; `test_feed_query_count_is_constant` checks this. Moderation reports point at their target through a `GenericForeignKey` (contenttypes), and a database constraint allows one vote per user per poll. `User` ↔ `Profile` is one-to-one; users own posts and posts own comments/messages through foreign keys; conversations expose a many-to-many participant relationship through `ConversationParticipant`; likes, bookmarks, follows, and reposts are unique relationship models.

## Setup

```bash
git clone https://github.com/life2harsh/fullstacklabpbl
cd vortex
python -m venv .venv
# Bash/Zsh:
source .venv/bin/activate
# Fish:
source .venv/bin/activate.fish
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Local SQLite is selected when `DATABASE_URL` is blank. For MySQL, set for example:

```dotenv
DATABASE_URL=mysql://root:root@127.0.0.1:3307/vortex_db
```

Then run `python manage.py migrate` again. Never commit `.env` or production secrets.

## Demonstration guide

```bash
python manage.py migrate
python manage.py seed      # demo users: aarav, diya, kabir... / vortex-demo-123, staff: admin / vortex-admin-123
python manage.py runserver
```

The seed passwords are for demos. On a deployment set `SEED_ADMIN_PASSWORD` so the staff account is not the public default. `seed` does nothing if demo data already exists (`--flush` to reseed).

1. Sign in as `aarav`. Browse the feed tabs, type in the search box (live results), page through older posts.
2. Create a post with a poll (open "Add a poll"). Vote, comment, reply in a thread, mention `@diya`.
3. Like, repost and bookmark from the feed without a page reload; open a profile to follow, block or report the user.
4. Open Messages as `aarav` in one browser and `diya` in a private window: messages and the typing indicator appear instantly.
5. Sign out, click *Forgot password?*, enter `aarav@vortex.test`; the reset email (with its link) is printed in the server terminal.
6. Click a `#hashtag` or a trending tag to filter the feed.
7. Open *My Activity* and download the CSV and PDF reports.
8. Sign in as `admin`: use *Moderation* to remove reported content, *Analytics* for platform stats and exports, and `/admin/` for model management and admin actions.

## Testing and checks

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

25 tests cover auth (including CSRF and deactivated users), password reset by email, the privacy of user JSON, profile and password forms, hashtags, posts with poll formsets, one vote per poll, ownership permissions, threaded comments and notifications, constant feed query count, live search partials, blocking, AJAX toggles, moderation, and CSV/PDF/analytics exports, and WebSocket chat (message push, typing, anonymous rejection) using `channels.testing`. GitHub Actions runs the checks and tests on every push.

## Syllabus mapping

| Module | Where it is in Vortex |
|---|---|
| 1. Python & Django fundamentals | Project/app structure, `settings.py` from `.env`, 8 apps, management command `seed` |
| 2. Views, URL routing, templates | App `urls.py` with named routes and `{% url %}`, function-based views passing context, DTL filters (`timesince`, `linebreaks`, `truncatechars`, `widthratio`) |
| 3. Template inheritance & static files | `base.html` → `layout.html` → pages, `{% include %}` partials incl. recursive comment threads, custom inclusion tag `{% avatar %}`, CSS/JS/images under `static/` |
| 4. Django ORM | One-to-one (`Profile`, `Poll`), one-to-many (posts, comments), many-to-many (`Post.tags`), many-to-many through (`ConversationParticipant`), self-FK (comment replies), generic FK (`Report`); CRUD; ModelForms and inline formsets; `annotate`, `Count`, `Exists`, `Q`, `F`, `TruncDate`; `Paginator` |
| 5. Authentication & Admin | Login/register/logout, password reset via email tokens, `login_required`, `staff_member_required`, ownership checks, password validation, customised `ModelAdmin` with inlines and actions |
| 6. Reporting & interactive apps | CSV via `csv`, PDF via ReportLab Platypus, AJAX toggles returning JSON, live search returning rendered HTML fragments, real-time chat via Django Channels WebSockets |

## Deployment

`render.yaml` is a Render blueprint: in Render choose *New → Blueprint*, pick this repository, and enter a `SEED_ADMIN_PASSWORD`. The app runs under Daphne (ASGI, so WebSockets work), WhiteNoise serves static files, and settings come from environment variables (`DEBUG=0`, `HTTPS=1` for secure cookies and redirects). The free plan's disk is temporary, so SQLite and uploads reset on every restart and `seed` refills demo data. For MySQL set `DATABASE_URL=mysql://...`; for real email set `EMAIL_BACKEND` and the `EMAIL_*` variables.

`docker compose up` runs the same server with MySQL.

## Future improvements

A Redis channel layer so chat works across several server processes, thumbnail generation for uploads, email notifications, and object storage for media in production.
