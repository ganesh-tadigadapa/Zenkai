# Zenkai

**Your opportunity radar.** — *Stop searching. Start discovering.*

Zenkai discovers opportunities scattered across the web — from internships and
hackathons to certifications, scholarships, programs, and student benefits — and
brings the ones relevant to you into one place.

It records where every opportunity came from and how far it has been
established, ranks everything against your profile with reasons you can read,
and never claims more confidence than it has.

<!-- Replace with a real screenshot before publishing. -->

---

## Why it exists

Opportunities that matter to students are scattered across company programme
pages, certification platforms, university portals, developer programmes,
newsletters and social posts. Nobody checks all of them, so students miss things
that were free and open to them the whole time.

Aggregators exist, but they tend to have two problems: they are stale, and they
do not tell you how confident they are. Zenkai is built around the opposite
principle — **every record carries its source, its verification status and the
date it was last checked**, and the interface never hides that.

---

## What is built

| Area | State |
|---|---|
| Database schema, models, migrations path | Complete |
| REST API (24 endpoints, OpenAPI docs) | Complete |
| Rule-based recommendation scoring | Complete, with visible reasons |
| Landing page, dashboard, feed, detail page | Complete |
| Cinematic 0→100% entrance sequence | Complete — plays once, skippable, honours reduced motion |
| Search, filtering, faceting, pagination | Complete |
| Saved opportunities and deadline tracking | Complete |
| Profile and preferences | Complete |
| Admin review queue (approve / reject / edit) | Complete |
| Accounts — sign-up, sign-in, sessions, password change | Complete |
| Direct enrol/apply destinations with type-aware CTAs | Complete — 49 of 54 records |
| Credential model — type, specialization, proctoring, assessment | Complete for the certifications vertical |
| Source registry — authority, discovery method, cadence | Complete |
| Raw source evidence and provenance trail | Complete |
| Change detection and mass-deletion guard | Complete |
| Live RSS/Atom discovery | Complete — real fetch, parse, relevance gate, provenance |
| Live official-API discovery | Complete — Microsoft Learn catalogue adapter |
| Web/sitemap connector | **Not implemented** — contract only |
| Source registry and compliance gate | Complete |
| Ingestion pipeline (extract → dedupe → verify) | Complete against the stub extractor |
| Connector network fetching (RSS / API / web) | **Not implemented** — interfaces only |
| LLM-backed extraction | **Not implemented** — stub provider only |
| Notification delivery | **Not implemented** — model and service only |
| Password reset by email | **Not implemented** — needs an email provider |
| OAuth (GitHub / Google) | **Not implemented** — provider seam in place |

The catalogue is **217 records**: 54 curated by hand and **163 discovered from
live sources** — Microsoft's certification catalogue API and Outreachy's
announcement feed. Everything discovered is `Needs verification` until a
reviewer confirms it; discovery never certifies its own output. Each carries a status —
`Curated` or `Needs verification` — and the product never presents them as
continuously checked live data.

**On discovery:** the RSS/Atom connector fetches for real. It obeys robots.txt
at request time, rate-limits per host, and never retries around a 401/403/429 —
those are a provider saying no. A relevance gate sits between fetching and
extraction because most of a real feed is not an opportunity: a vendor's
release feed is a hundred product announcements, and without the gate those
would become a hundred records no student can apply to.

Run it with `make discover`. Certifications went from 10 to 153 this way.

**On destinations:** every record carries the provider's authoritative page,
and 49 of 54 also carry the exact page where a student can start, enrol,
register or apply — so the button goes there rather than to a homepage. The
other 5 fall back to the official source and say so. No URL was invented to
close that gap.

**On deadlines:** Zenkai shows a date only where the official source publishes
one. The catalogue's programmes are either continuously open or announce dates
each cycle, so most records read "Deadline not listed" rather than carrying a
guess. The deadline tracker is fully built and tested; it fills in when source
checking supplies real dates.

---

## Tech stack

**Backend** — Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL
(SQLite-portable), pytest.

**Frontend** — Next.js 16 (App Router, React Server Components), TypeScript,
Tailwind CSS v4, server actions for all mutations.

No component library, no icon package, no state manager, no ORM beyond
SQLAlchemy. The dependency list is deliberately short.

---

## Run it locally

Requires Python 3.11+ and Node 20+. PostgreSQL is optional.

```bash
# 1. Install
make install

# 2. Create tables and load the seed catalogue
make seed

# 3. Backend on :8000  (leave running)
make backend

# 4. Frontend on :3000 (in a second terminal)
make frontend
```

Open <http://localhost:3000>. API docs are at <http://localhost:8000/docs>.

Browsing needs no account. To see saved items, matching and the review queue,
sign in with the seeded accounts — the sign-in page shows them in development:

| Account | Email | Password |
|---|---|---|
| Student | `student@zenkai.dev` | `zenkai-demo-2026` |
| Reviewer | `reviewer@zenkai.dev` | `zenkai-review-2026` |

**Change both before any public deployment.**

Without `make`, see [DEVELOPMENT.md](DEVELOPMENT.md) for the raw commands.

### Using PostgreSQL

SQLite is the default so the project runs with no database server. To use
PostgreSQL instead:

```bash
docker compose up -d
export DATABASE_URL=postgresql+psycopg://studentos:studentos@localhost:5432/studentos
cd backend && .venv/bin/python -m app.seed.run --reset
```

The schema is written for PostgreSQL and stays portable by using `JSON` rather
than `JSONB` and string-backed enums rather than native enum types.

---

## Environment variables

Copy `.env.example` to `backend/.env` and `frontend/.env.local`. Never commit a
filled-in `.env`.

### Backend (`backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./studentos.db` | SQLAlchemy URL. Use `postgresql+psycopg://…` in production. |
| `ENV` | `development` | `development` auto-creates tables at startup. |
| `CORS_ORIGINS` | `http://localhost:3000,…` | Comma-separated allowed browser origins. |
| `ADMIN_TOKEN` | `dev-admin-token` | **Change this.** Required by every `/api/v1/admin/*` route. |
| `DEMO_USER_EMAIL` | `student@zenkai.dev` | The seeded demo student. |
| `DEMO_USER_PASSWORD` | `zenkai-demo-2026` | **Change this.** Password for the seeded demo student. |
| `DEMO_ADMIN_EMAIL` | `reviewer@zenkai.dev` | The seeded reviewer. |
| `DEMO_ADMIN_PASSWORD` | `zenkai-review-2026` | **Change this.** Password for the seeded reviewer. |
| `ALLOW_DEMO_FALLBACK` | unset | When true, a request with no session resolves to the demo student. Defaults to on in development, off elsewhere. Leave it off in production. |
| `AI_PROVIDER` | `stub` | Extraction provider. `stub` is heuristic and needs no key. |
| `AI_API_KEY` | — | Key for a real provider, once one is implemented. |
| `AI_MODEL` | `claude-sonnet-5` | Model id passed to the provider. |

### Frontend (`frontend/.env.local`)

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL. |
| `ZENKAI_ADMIN_TOKEN` | `dev-admin-token` | Sent as `X-Admin-Token` from the server only. Must match the backend's `ADMIN_TOKEN`. Not `NEXT_PUBLIC_`, so it never enters the browser bundle. |

---

## Testing

```bash
make test          # 295 backend tests
make lint          # tsc --noEmit + eslint
make build         # production build of the frontend
```

Tests cover opportunity creation and retrieval, filtering, search across all
indexed fields, deadline sorting and bucketing, verification status transitions,
saving, recommendation scoring, admin approval and rejection, the ingestion
pipeline's deduplication and compliance gates, the catalogue's editorial rules
— including that no record invents a deadline or overstates its verification —
and authentication: password hashing and salting, session expiry and
revocation, and that one account's saved list and preferences are invisible to
another. See [DEVELOPMENT.md](DEVELOPMENT.md).

---

## Deploying

See [DEPLOYMENT.md](DEPLOYMENT.md). In short: the frontend deploys to Vercel
with **Root Directory set to `frontend`**, and needs `NEXT_PUBLIC_API_URL`
pointing at a hosted backend. The FastAPI service is a separate deployment —
Vercel does not host it.

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — how the system is put together and why
- [DATABASE.md](DATABASE.md) — schema, indexes, and the reasoning behind it
- [DEVELOPMENT.md](DEVELOPMENT.md) — running, testing, and adding to the project

---

## What Zenkai does not claim

These limits are stated on the product itself, not just here.

- **It does not scan the internet.** It checks sources that a human registered,
  on a schedule. Coverage is exactly as wide as that list.
- **"Verified" means a person checked the official source on the date shown.**
  It is not a continuous live check, and programme terms change without notice.
- **Match scores are fixed rules, not machine learning.** Every point awarded is
  shown to the student as a written reason. A score does not predict acceptance.
- **Deadlines marked `~` are estimates** derived from a programme's usual annual
  cycle, not announced dates.
- **Sources that prohibit automated access are never fetched.** They are
  recorded in the sources table with `robots_allowed = false` specifically so
  the system has an explicit record of what it must not touch.

---

## Roadmap

1. **Password reset by email.** Accounts exist, but a forgotten password is
   currently unrecoverable. This needs an email provider and is the most
   user-facing gap.
2. **Implement one connector end to end** — RSS is the natural first choice,
   since feeds are published for machine consumption.
3. **Plug in a real extraction model** behind the existing `AIClient` interface
   and compare its confidence against reviewer decisions.
4. **Scheduler** to drive `due_sources()` on a cadence.
5. **OAuth sign-in** (GitHub, Google) behind the existing provider seam.
6. **Notification delivery** — the model and service seam already exist.
7. **Chrome extension** consuming the same public API.
