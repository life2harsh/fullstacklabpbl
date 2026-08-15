# Vortex — Django Full-Stack Social Network

Vortex is a course-ready Python/Django social network for sharing posts, discussing ideas, following people, messaging, and reviewing community reports. The migration keeps the original noir visual identity and vanilla JavaScript interactions while replacing the FastAPI/SQLAlchemy backend with Django MVT, Django ORM, session authentication, templates, forms, admin, and report exports.

## Problem statement

Small communities need one place to publish updates, discover people, have conversations, and manage harmful or unwanted content. Vortex demonstrates that workflow as a multi-page full-stack web application rather than a collection of disconnected demos.

## Features

- Registration, login, logout, password hashing, sessions, protected routes, and ownership checks
- Feed, post detail, profiles, profile editing, media uploads, comments, nested replies, mentions, likes, reposts, bookmarks, follows, blocking, notifications, and messaging
- Poll and poll-vote models with Django ORM relationships
- AJAX/fetch actions with Django CSRF protection and asynchronous `/search/?q=...`
- Django Admin for users/profiles, posts/comments, interactions, messages, notifications, polls, and moderation reports
- User activity CSV export and dynamically generated PDF activity report
- Responsive frontend reusing the original Vortex CSS, layout, and interaction patterns

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
├── reports/                # CSV/PDF report endpoints and report form
├── templates/              # inherited Django templates
├── static/                 # original Vortex styles plus AJAX helper
└── media/                  # local uploads, ignored by git
```

The application uses function-based Django views, app-level URL modules, Django Template Language, a reusable `templates/base.html`, ModelForms, QuerySets, and explicit relationship models. `User` ↔ `Profile` is one-to-one; users own posts and posts own comments/messages through foreign keys; conversations expose a many-to-many participant relationship through `ConversationParticipant`; likes, bookmarks, follows, and reposts are unique relationship models.

## Setup

```bash
git clone https://github.com/life2harsh/fullstacklabpbl
cd vortex
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
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

1. Register two users and log in; open `/admin/` with the superuser.
2. Create, edit, delete, like, bookmark, repost, and comment on a post. Try a nested reply and an `@mention`.
3. Search from the feed or call `/search/?q=django`; results are returned by an ORM-backed JSON view without a full page refresh.
4. Follow/block another user, send messages, and mark notifications read.
5. Open `/reports/activity/` and download CSV and PDF exports generated from database data.
6. Review submitted moderation reports in Django Admin or the staff-only `/moderation/` page.

## Testing and checks

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

The test suite covers registration/login, protected routes, post CRUD ownership, comments, likes/follows, search, exports, and conversation relationships.

## Course outcomes mapping

| Outcome | Vortex evidence |
|---|---|
| CO1: Python + Django fundamentals | Python settings, models, forms, function-based views, and management commands |
| CO2: Views, URLs, templates, inheritance | App URL modules, `base.html`, inherited multi-page templates, context in reports/moderation |
| CO3: ORM, CRUD, forms, relationships | ModelForms, QuerySets, validation, post/comment/message CRUD, one-to-one/one-to-many/many-to-many relationships |
| CO4: Authentication, Admin, validation, export | Django sessions, password hashing, `login_required`, staff admin, ModelForms, CSV and PDF reports |
| CO5: AJAX search and reporting | Fetch-based likes/bookmarks/messages/notifications and `/search/?q=...`, CSV/PDF endpoints |

## Future improvements

Add WebSocket delivery for messages, richer poll UI, thumbnail processing and upload virus scanning, pagination/infinite scroll, email notification preferences, and production object storage for media.
