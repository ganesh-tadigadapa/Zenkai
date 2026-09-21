# Development

## Prerequisites

- Python 3.11 or newer (3.11 is what the venv is built with)
- Node 20 or newer
- Docker, only if you want PostgreSQL instead of SQLite

---

## Setup without `make`

```bash
# Backend
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ../.env.example .env            # then edit
.venv/bin/python -m app.seed.run   # create tables + load the catalogue
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\nZENKAI_ADMIN_TOKEN=dev-admin-token\n' > .env.local
npm run dev
```

- App: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

`ZENKAI_ADMIN_TOKEN` must match the backend's `ADMIN_TOKEN` or `/admin` will
show an authorisation error.

---

## Switching to PostgreSQL

```bash
docker compose up -d
cd backend
export DATABASE_URL=postgresql+psycopg://studentos:studentos@localhost:5432/studentos
.venv/bin/python -m app.seed.run --reset
```

Set the same `DATABASE_URL` in `backend/.env` to make it permanent.

---

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q        # all 295
.venv/bin/python -m pytest tests/test_matching.py -v
.venv/bin/python -m pytest -k "deadline"
```

Each test runs against a fresh in-memory SQLite database with the `db_session`
dependency overridden, so tests never touch your development data and can run in
any order.

| File | Covers |
|---|---|
| `test_opportunities.py` | Creation, slugs, retrieval by id/slug, every filter, search across title/organisation/description/skills/tags, deadline sorting, pagination, expiry, facets |
| `test_matching.py` | Scoring bounds, each weighted signal in isolation, reason text, relevance ordering through the API |
| `test_saved_and_deadlines.py` | Idempotent saving, unsaving, saved-state on the feed, active/expired split, deadline bucketing and ordering, dashboard stats |
| `test_admin.py` | Token enforcement, queue ordering by confidence, approve/reject/edit, audit trail, non-reviewable field protection, manual creation and dedup |
| `test_pipeline.py` | Stub extraction, deduplication (exact and fuzzy), verification routing, `robots_allowed` and inactive-source refusal, scheduler due-ness, pipeline idempotency |
| `test_profile_and_notifications.py` | Identity resolution, preference persistence, preference changes affecting recommendations, notification queueing and dispatch |
| `test_discovery.py` | RSS and Atom parsing, unparseable dates staying None, non-feed bodies raising rather than looking empty, the relevance gate accepting opportunities and rejecting product announcements and senior job posts, the connector refusing blocked and inactive sources, a 403 not being retried, and a feed becoming records without inventing cost, deadline or destination |
| `test_intelligence_engine.py` | UNKNOWN never written as NO, only genuine certifications typed as professional, authority gating belief separately from access, discovery preference order, change detection, the mass-deletion guard, raw evidence stored without credentials, and provenance surviving deduplication |
| `test_destinations.py` | Direct destination preferred over source, official source as fallback, button wording per opportunity type (an exam never says "Start course"), explicit action overrides, malformed records degrading instead of crashing, and the catalogue's URL corrections |
| `test_auth.py` | Password hashing and per-hash salting, session token digests, expiry and purging, logout revocation, malformed Authorization headers, cascade cleanup, non-enumerable login errors, password change revoking other devices, and isolation of saved items and preferences between accounts |
| `test_seed_integrity.py` | The catalogue's editorial rules: no invented deadlines, no record overstating its verification, https official sources, valid enum values, learning platforms not labelled certifications, and blocked sources recorded with a reason |

Fixtures and factories live in `tests/conftest.py`. `make_opportunity` accepts
plain strings or enum members so tests read naturally.

---

## Frontend checks

```bash
cd frontend
npx tsc --noEmit   # types
npm run lint       # eslint
npm run build      # production build
```

All three must pass. The build output should show `/` as static and every
`(app)` route as dynamic — that is the intended rendering strategy, not a
warning.

---

## Adding an opportunity by hand

Through the API:

```bash
curl -X POST http://localhost:8000/api/v1/admin/opportunities \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Token: dev-admin-token' \
  -d '{
    "title": "Example Student Program",
    "organization_name": "Example Corp",
    "category": "tech_benefits",
    "opportunity_type": "software",
    "summary": "A short description of what this offers students.",
    "description": "A longer description, at least a few sentences.",
    "application_url": "https://example.com/apply",
    "source_url": "https://example.com/program"
  }'
```

It lands in `/admin` as `needs_review`. Submitting the same payload twice
returns the existing record rather than creating a duplicate.

To add it to the seed catalogue instead, append a dict to the relevant list in
`backend/app/seed/data.py` and re-run the seeder. Read the editorial rules at
the top of that file first — descriptions must state only what the official page
states, and deadlines and costs appear only where the source publishes them.
`tests/test_seed_integrity.py` enforces those rules, so a record that breaks
them fails the suite rather than reaching students.

---

## Running discovery

```bash
make discover                                   # every due, enabled source
cd backend && .venv/bin/python run_discovery.py "Outreachy announcements"
```

Sources that are disabled or disallow automated access are skipped. Every
attempt is recorded in `source_checks`, including the failures.

**Tests never touch the live web.** An autouse fixture in `tests/conftest.py`
patches httpx's real transport so an accidental network call fails loudly;
use `FakeFetcher` with a fixture body instead.

## Adding an API adapter

Feeds share a format; APIs do not. `APIConnector` does the fetching and a
per-provider adapter under `app/ingestion/adapters/` does the mapping.

1. Subclass `ApiAdapter`, set `url_marker` and `name`, implement
   `to_documents`.
2. Register it in `adapters/__init__.py`.
3. In the document metadata, set `catalogue` when the endpoint returns one kind
   of thing (relevance is then established by construction), and
   `unpublished_fields` for anything the API does not carry — that stops the
   extractor's prose heuristics inventing a value the source never stated.

A source whose URL matches no adapter fails loudly rather than being guessed at.

## Adding a connector

1. Subclass `SourceConnector` in `app/ingestion/connectors/`, set
   `source_type`, and implement `_fetch(source) -> Iterable[RawDocument]`.
   Do not override `fetch` — it runs the compliance gate.
2. Register the class in `connectors/__init__.py`'s `REGISTRY`.
3. Add a row to `sources` (via `/api/v1/admin/sources` or the seed file) with an
   accurate `robots_allowed` and a note explaining how you established it.
4. The pipeline handles extraction, deduplication, verification and routing to
   the review queue with no further changes.

Constraints, enforced in code and tests: never fetch a source with
`robots_allowed = false` or `active = false`, never work around CAPTCHAs,
authentication or rate limits, and identify the client honestly via the
`USER_AGENT` constant.

---

## Adding an AI provider

Implement the six methods of `app/ai/base.AIClient` and register the class in
`app/ai/__init__.get_ai_client()`, keyed on `AI_PROVIDER`. Read credentials from
the environment via `settings`, never from the database.

Keep confidence honest: `AUTO_APPROVE_CONFIDENCE` is 0.95, and a provider that
returns inflated scores will push unchecked records past human review. A test
asserts the stub never reaches that threshold; add the equivalent test for any
new provider.

---

## Conventions

- **Backend.** Type hints everywhere; `from __future__ import annotations` at
  the top of every module. Routers stay thin. Business rules live in services,
  query construction in repositories.
- **Frontend.** Server Components by default; add `"use client"` only for a
  named interactive reason. Mutations go through server actions in
  `lib/actions.ts`, never `fetch` from the browser.
- **Styling.** Only semantic token classes (`bg-surface`, `text-muted`,
  `border-border`). Never a raw Tailwind palette colour, or the two themes will
  drift apart.
- **Colour meaning.** The accent is the brand. Green, amber and rose mean
  verification state and deadline urgency, and nothing else.
- **Honesty.** If the product cannot verify something, the interface says so.
  This is a product requirement, not a nicety.

---

## Troubleshooting

**`/admin` shows "page not found"** — you are signed in as a student. Sign in
as `reviewer@zenkai.dev`; the review queue is only reachable by an account with
`is_admin` set.

**Every protected route bounces to `/login`** — expected when signed out. Use
the credentials shown on the sign-in page in development.

**Every page shows "Could not load opportunities"** — the backend is not running
or `NEXT_PUBLIC_API_URL` is wrong. Check `curl http://localhost:8000/health`.

**Stuck on the sign-in page, or a page renders only its header** — you are
holding a session cookie whose session no longer exists, usually because the
database was reseeded. Signing in again fixes it; the page now says "Your
session has ended" rather than looping.

**Sign-in fails for the seeded accounts** — the database predates passwords, or
the seeder never ran. Run `python -m app.seed.run --reset`.

**Saving fails with 404 after re-seeding** — `--reset` regenerates every id, and
a page rendered before the reset holds stale ones. Reload the page.

**Stale data in development** — delete `frontend/.next` and restart `npm run dev`.
