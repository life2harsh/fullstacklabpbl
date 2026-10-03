# Vortex — Django Full-Stack Social Network

Vortex is a course-ready Python/Django social network for sharing posts, discussing ideas, following people, messaging, and reviewing community reports. The migration keeps the original noir visual identity and vanilla JavaScript interactions while replacing the FastAPI/SQLAlchemy backend with Django MVT, Django ORM, session authentication, templates, forms, admin, and report exports.

## Problem statement

Small communities need one place to publish updates, discover people, have conversations, and manage harmful or unwanted content. Vortex demonstrates that workflow as a multi-page full-stack web application rather than a collection of disconnected demos.

## Features

- Registration, login (email or username), logout, password change and account deletion using Django forms, `AuthenticationForm`, `PasswordChangeForm` and session auth
- Server-rendered feed with Latest / Following / Trending / Bookmarks tabs, pagination and live (debounced AJAX) search over posts and people
- Post CRUD with image uploads, optional polls built with an inline formset, threaded comment replies, `@mentions`
- AJAX likes, reposts, bookmarks, follows and blocks that return JSON and update counts in place
- Notifications and messaging, with unread badges supplied by a context processor and refreshed by polling
- Report button on posts, comments and users; a staff moderation queue to review, dismiss or remove content; matching Django Admin actions
- Personal activity report and staff platform analytics (date-range form, aggregate QuerySets), both exportable as CSV and PDF
- Customised Django Admin: inlines, annotated list columns, filters, date hierarchy and CSV export actions
- `manage.py seed` command for realistic demo data

## Technology stack

Python 3.11+ · Django 5.2 · Django ORM · SQLite for local development · MySQL through `DATABASE_URL` · vanilla HTML/CSS/JavaScript · PyMySQL · Pillow · ReportLab · Gunicorn

## Architecture

```text
vortex/
├── manage.py
├── vortex/                 # settings, root URLs, WSGI, ASGI
├── accounts/               # registration, sessions, Profile, follows, blocks
├── posts/                  # Post, Comment, Poll, Mention, CRUD and search
├── interactions/           # likes, reposts, bookmarks, follows/block actions
├── messaging/              # Conversation, participants, Message CRUD
├── notifications/          # notification feed and read state
├── moderation/             # user-submitted reports and staff queue
├── reports/                # activity + analytics pages, CSV/PDF exports
├── core/                   # shared helpers, badge context processor, {% avatar %} tag, seed command
├── templates/              # inherited Django templates
├── static/                 # original Vortex styles plus AJAX helper
└── media/                  # local uploads, ignored by git
```

Pages are rendered with function-based views and the Django Template Language. `base.html` → `layout.html` (sidebar) → page templates, with reusable partials in `templates/partials/` (post card, comment thread, poll, report form, form fields). JavaScript is limited to progressive enhancement in `static/js/app.js`: CSRF-aware fetch, toggle buttons, live search and badge polling. Chat is the only page rendered on the client.

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

The seed passwords are for local demos only. Never run `seed` against a deployed database.

1. Sign in as `aarav`. Browse the feed tabs, type in the search box (live results), page through older posts.
2. Create a post with a poll (open "Add a poll"). Vote, comment, reply in a thread, mention `@diya`.
3. Like, repost and bookmark from the feed without a page reload; open a profile to follow, block or report the user.
4. Check Alerts and Messages; badges update automatically.
5. Open *My Activity* and download the CSV and PDF reports.
6. Sign in as `admin`: use *Moderation* to remove reported content, *Analytics* for platform stats and exports, and `/admin/` for model management and admin actions.

## Testing and checks

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

21 tests cover auth (including CSRF and deactivated users), the privacy of user JSON, profile and password forms, posts with poll formsets, one vote per poll, ownership permissions, threaded comments and notifications, constant feed query count, live search partials, blocking, AJAX toggles, moderation, and CSV/PDF/analytics exports.

## Syllabus mapping

| Module | Where it is in Vortex |
|---|---|
| 1. Python & Django fundamentals | Project/app structure, `settings.py` from `.env`, 8 apps, management command `seed` |
| 2. Views, URL routing, templates | App `urls.py` with named routes and `{% url %}`, function-based views passing context, DTL filters (`timesince`, `linebreaks`, `truncatechars`, `widthratio`) |
| 3. Template inheritance & static files | `base.html` → `layout.html` → pages, `{% include %}` partials incl. recursive comment threads, custom inclusion tag `{% avatar %}`, CSS/JS/images under `static/` |
| 4. Django ORM | One-to-one (`Profile`, `Poll`), one-to-many (posts, comments), many-to-many through (`ConversationParticipant`), self-FK (comment replies), generic FK (`Report`); CRUD; ModelForms and inline formsets; `annotate`, `Count`, `Exists`, `Q`, `F`, `TruncDate`; `Paginator` |
| 5. Authentication & Admin | Login/register/logout, `login_required`, `staff_member_required`, ownership checks, password validation, customised `ModelAdmin` with inlines and actions |
| 6. Reporting & interactive apps | CSV via `csv`, PDF via ReportLab Platypus, AJAX toggles returning JSON, live search returning rendered HTML fragments, badge polling |

## Future improvements

WebSocket delivery for chat (Django Channels), thumbnail generation for uploads, email notifications, and object storage for media in production.
