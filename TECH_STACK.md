# Zenkai — How the Whole Thing Works

A walkthrough of every part of the stack: what each piece is, why it's there,
and how they talk to each other.

---

## 1. The big picture

```
                 ┌──────────────────────────────────────────┐
  Student's  ──▶ │  FRONTEND  · Next.js on Vercel            │
  browser        │  pages, login cookie, server actions      │
                 └───────────────┬──────────────────────────┘
                                 │ HTTPS + "Authorization: Bearer <token>"
                 ┌───────────────▼──────────────────────────┐
                 │  BACKEND  · FastAPI on Render             │
                 │  auth, opportunities, matching, saving    │
                 └───────────────┬──────────────────────────┘
                                 │ SQL
                 ┌───────────────▼──────────────────────────┐
                 │  DATABASE  · PostgreSQL on Neon           │
                 └───────────────▲──────────────────────────┘
                                 │ writes new opportunities
                 ┌───────────────┴──────────────────────────┐
                 │  DISCOVERY  · GitHub Actions, every 6h    │
                 │  reads official sources → cleans → saves  │
                 └──────────────────────────────────────────┘
```

Four parts, each hosted somewhere different:

| Part | Tech | Hosted on | Job |
|---|---|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4 | Vercel | Everything the student sees |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic | Render | Logic, auth, data access |
| Database | PostgreSQL 16 | Neon | Stores everything |
| Discovery | Python scripts | GitHub Actions (cron) | Finds new opportunities every 6 hours |

The website never talks to the database directly; it always goes through the
backend.

---

## 2. Frontend — what the student sees

**Folder:** `frontend/`

### The tools

- **Next.js 16** — the React framework. Handles routing, server rendering, and
  building the site.
- **React 19** — the UI library. Pages are built from components.
- **TypeScript** — JavaScript with types, so mistakes are caught before running.
- **Tailwind CSS v4** — styling via small utility classes (`text-muted`,
  `rounded-full`) written straight in the markup.
- **ESLint** — catches code problems.

### How pages are organised (App Router)

Each folder under `src/app/` is a URL:

```
src/app/
  page.tsx                     →  /            (landing page)
  (auth)/login/page.tsx        →  /login
  (auth)/signup/page.tsx       →  /signup
  (app)/opportunities/         →  /opportunities and /opportunities/[slug]
  (app)/(private)/dashboard/   →  /dashboard   (needs a session)
  (app)/(private)/saved/       →  /saved
  (app)/(private)/deadlines/   →  /deadlines
  (app)/(private)/profile/     →  /profile
  (app)/(private)/admin/       →  /admin       (reviewers only)
  api/health/route.ts          →  /api/health  (pings the backend)
```

Folders in brackets like `(auth)` and `(private)` group pages and share a
layout, but don't appear in the URL.

### Server vs client components

- **Server Components** (the default) run on Vercel's server. They fetch data
  from the backend and send finished HTML to the browser. Fast, and secrets never
  reach the browser.
- **Client Components** (files starting with `"use client"`) run in the browser.
  Only the interactive bits use this: user menu, theme toggle, intro animation,
  the cursor spotlight, the guest button's loading state.

### Key files in `src/lib/`

| File | What it does |
|---|---|
| `api.ts` | One typed wrapper around every backend endpoint. Runs on the server only, and attaches the login token to each request automatically. |
| `actions.ts` | **Server Actions**: functions forms call directly (`guestAction`, `loginAction`, `signupAction`, `claimAccountAction`, `toggleSaveAction`…). They run on the server, call the backend, and set or clear the login cookie. |
| `session.ts` | Reads, sets and deletes the login cookie. |
| `require-user.ts` | Asks the backend "who is this?" and redirects to sign-in if nobody. |
| `types.ts` | TypeScript shapes of everything the backend returns. |
| `format.ts` | Labels and helpers: "3 days left", category names, cost text. |

### Guarding private pages

Two layers:

1. **`proxy.ts`** runs before every request. If you open `/dashboard` with no
   login cookie at all, it redirects to `/login?next=/dashboard`. It's cheap: it
   only checks that the cookie exists.
2. **`(private)/layout.tsx`** is the real gate. It asks the backend whether the
   session is actually valid. An expired cookie sends you to
   `/login?expired=1`.

### Styling and themes

All colours are CSS variables in `globals.css` (`--bg`, `--text`, `--accent`…),
with one set for light mode and one for dark. The theme toggle just switches
which set is active. A tiny script in `layout.tsx` applies your saved theme
before the page paints, so there's no flash.

### The landing page

`app/page.tsx` is **fully static**: built once at deploy time, calls no API,
loads instantly.

- **Animations** are pure CSS keyframes in `globals.css`: blur-in entrance,
  rotating headline word, radar rings, drifting glow, glowing button border,
  marquee strips, feature card loops, scroll reveal.
- **Instrument Serif** (Google font) for the italic accent words.
- **`Spotlight.tsx`** — the glow that follows your mouse. It writes the cursor
  position to CSS variables, so moving the mouse never re-renders React.
- **`IntroSequence.tsx`** — the once-per-visitor intro. It remembers you've seen
  it in `localStorage`. While it plays, the page's entrance animation is paused,
  then released as the intro fades out.
- Anyone with "reduce motion" on in their system settings gets a still version.

---

## 3. Backend — the brain

**Folder:** `backend/`

### The tools

- **FastAPI** — the web framework. Defines endpoints and auto-generates API docs
  at `/docs`.
- **Uvicorn** — the server that runs FastAPI.
- **Pydantic** — validates every request and response against a schema.
- **SQLAlchemy 2** — talks to the database using Python classes instead of raw
  SQL.
- **psycopg** — the PostgreSQL driver.
- **httpx** — makes outbound HTTP requests (used by discovery).
- **argon2-cffi** — password hashing.
- **pytest** — the test suite (365 tests).

### Layers

Every request flows the same way:

```
router  →  service  →  repository  →  model  →  database
(HTTP)     (logic)     (queries)      (tables)
```

| Layer | Folder | Rule |
|---|---|---|
| Routers | `app/api/v1/routers/` | Only parse the request and return the response. No logic. |
| Services | `app/services/` | The decisions: matching, saving, deadlines, auth. |
| Repositories | `app/repositories/` | Query building: filters, search, sorting. |
| Models | `app/models/` | Database tables as Python classes. |
| Schemas | `app/schemas/` | Pydantic shapes for what goes in and comes out. |

`opportunity_repository.apply_filters` is the single definition of "what a
student may see". The feed, deadlines page and dashboard all use it, so they
can never disagree.

### The API routes (all under `/api/v1`)

| Router | Examples |
|---|---|
| `auth` | `/auth/signup`, `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/guest`, `/auth/claim`, `/auth/change-password` |
| `opportunities` | `/opportunities` (search, filter, sort), `/opportunities/{slug}`, `/opportunities/facets`, `/categories` |
| `dashboard` | `/dashboard`, `/stats`, `/recommendations` |
| `saved` | save and unsave opportunities, list saved |
| `deadlines` | upcoming deadlines for saved items |
| `profile` | read and update name and matching preferences |
| `admin` | review queue: approve, reject, edit records |

---

## 4. Database

**PostgreSQL 16**, hosted free on **Neon**. Locally it can also run on
**SQLite** with no setup; the code stays compatible with both.

### Main tables

```
organizations ──< opportunities >── sources
                       │
        ┌──────────────┼──────────────────┐
        │              │                  │
saved_opportunities  verification_reviews  notifications
        │
      users ──── user_preferences
        │
   user_sessions
```

| Table | Holds |
|---|---|
| `opportunities` | One row per opportunity: title, category, deadline, cost, location, source URL, verification status, skills, tags… |
| `organizations` | Who offers it (Google, MLH, a university…) |
| `sources` | Every place Zenkai reads from, with trust level, check frequency, and whether automated access is allowed |
| `users` | Accounts: email, name, password hash, `auth_provider` (`password` or `guest`) |
| `user_preferences` | Degree, field, year, location, skills, interests, preferred categories — drives matching |
| `user_sessions` | Active logins (only a hash of the token is stored) |
| `saved_opportunities` | What each user saved |
| `verification_reviews` | Append-only log of every approve, reject and edit |
| `raw_source_documents` / `opportunity_provenance` | What each source originally returned, and which record came from which document |
| `credential_details` | Extra fields for certifications (exam fee, proctoring…) |

### Design choices worth knowing

- **Six categories are a fixed enum**, not a table: internships, hackathons,
  certifications, scholarships, programs, tech benefits.
- **All times are stored in UTC.** A custom column type keeps that consistent
  on both Postgres and SQLite.
- **Deadlines count calendar days**, so something closing at 9am today stays
  visible all day.
- **Duplicates are blocked by the database itself:** each record has a
  `content_hash` (SHA-256 of title + organisation + URL) with a unique
  constraint.
- **Unknown stays unknown.** If a source doesn't state a cost or deadline, it's
  stored as unknown and shown as "not listed", never guessed.

---

## 5. Authentication — how login works

### Passwords

- Hashed with **Argon2id** (the current recommended algorithm). The real
  password is never stored.
- Minimum 10 characters.
- Login gives the same error for "wrong email" and "wrong password", so nobody
  can probe which emails have accounts.

### Sessions (not JWTs)

1. On login, the backend creates a random 32-byte token.
2. It stores only the **SHA-256 hash** of that token in `user_sessions`, with a
   30-day expiry.
3. It returns the real token once, to the Next.js server.
4. Next.js puts it in an **httpOnly cookie** (`zenkai_session`). Browser
   JavaScript can't read it, so an XSS bug can't steal it.
5. On every request, Next.js forwards it to the backend as
   `Authorization: Bearer <token>`.
6. Logout deletes the session row, so it's revoked instantly. (That's the main
   reason for sessions over JWTs: JWTs can't be revoked before they expire.)
7. Changing your password signs out every device.

### Guest accounts (one-click "Get started")

1. Clicking **Get started** calls `POST /auth/guest`.
2. The backend creates a user with `auth_provider = "guest"`, no password, and a
   placeholder email like `guest-a1b2c3@guest.zenkai.invalid`.
3. A normal session starts, so the guest can save things and set preferences
   right away.
4. Later, from the profile page, the guest can **save their account**
   (`POST /auth/claim`): add name, email and password. Same account, so
   everything they saved stays.
5. A guest who signs out without saving loses the account, and the menu warns
   about that.

### Reviewers (admin)

Users with `is_admin = true` can open `/admin`. Scripts can use a shared
`ADMIN_TOKEN` header instead.

---

## 6. Discovery — how opportunities get in

This is the core of the product: a **trust pipeline**, not just a scraper.

### When it runs

A **GitHub Actions** workflow (`.github/workflows/discovery.yml`) runs every
6 hours. It connects to the Neon database and runs `backend/run_discovery.py`.

### The pipeline

```
SOURCES ─▶ FETCH ─▶ RAW DOCUMENT ─▶ EXTRACT ─▶ RELEVANCE ─▶ DEDUPLICATE
                                                                │
              DATABASE ◀── HUMAN REVIEW ◀── VERIFY ◀────────────┘
```

| Stage | Where | What happens |
|---|---|---|
| **Sources** | `seed/sources.py`, `models/source.py` | ~20 registered sources: Devpost, MLH, Unstop, GitHub Education, Microsoft Learn, Outreachy, Google Summer of Code, SimplifyJobs, AWS, Azure… Each has a type (RSS, web page, API), a trust level and a check frequency. |
| **Permission check** | connectors | A source with `robots_allowed = false` is never fetched. LinkedIn is registered specifically as "never touch". |
| **Fetch** | `ingestion/fetcher.py` | The only place that makes outbound requests. Honest User-Agent, obeys `robots.txt` and crawl delays, rate-limits per host, timeouts. It never retries around a 401, 403 or 429. |
| **Connectors** | `ingestion/connectors/` | One per source type: RSS/Atom feeds, web pages, APIs. |
| **Adapters** | `ingestion/adapters/` | Provider-specific code that turns each API's JSON into a standard shape: `devpost`, `mlh`, `unstop`, `microsoft_learn`, `github_pack`, `simplify`. |
| **Raw documents** | `models/provenance.py` | What the source returned is saved *before* anything interprets it, as an audit trail and so it can be re-processed later. |
| **Extraction** | `ingestion/extraction.py`, `ai/` | Pulls out title, deadline, eligibility, cost, category. Right now a rule-based "stub" (regex and keywords). It sits behind an AI interface, so a real LLM can be swapped in by writing one class. |
| **Relevance** | `ingestion/relevance.py` | Drops things that aren't one of the six categories. |
| **Deduplication** | `ingestion/deduplication.py` | Exact match by content hash, plus title-similarity within the same organisation to catch re-posts. A duplicate adds a provenance link instead of a new row. |
| **Verification** | `ingestion/verification.py` | Plausibility checks produce a confidence score. Auto-approve needs 0.95, but the stub caps itself at 0.65, so automated records always go to a human. |
| **Monitoring** | `ingestion/monitoring.py` | Detects changes and guards against a source suddenly "deleting" everything (usually a broken fetch, not real removals). |
| **Expiry** | `services/opportunity_service.py` | Past-deadline records are marked expired. |

### Verification labels students see

| Status | Meaning |
|---|---|
| `curated` | A person wrote it from the official page |
| `source_checked` | A reviewer confirmed it against the official source |
| `needs_review` | Found automatically; not yet confirmed (shown as "Needs verification") |
| `expired` | Closed or past deadline |
| `rejected` | A reviewer rejected it |

---

## 7. Matching — "Ranked for you"

`services/matching.py` scores every opportunity against your profile using
**fixed weights**. There's no machine learning, and every point comes with a
written reason.

| Factor | Max points |
|---|---|
| Category fit | 30 |
| Interests | 25 |
| Skills | 20 |
| Location or remote fit | 10 |
| Deadline relevance | 10 |
| Cost | 5 |
| **Total** | **100** |

The score is about fit, not a prediction of whether you'll be accepted.

---

## 8. Hosting and automation

| Service | Role | Notes |
|---|---|---|
| **Vercel** | Frontend | Root directory is `frontend/`. Redeploys on every push to `main`. Needs `NEXT_PUBLIC_API_URL` pointing at the backend. |
| **Render** | Backend | Set up by `render.yaml`. Free plan: sleeps after 15 minutes idle, so the first request after that is slow. The build also runs the seeder. |
| **Neon** | Database | Free PostgreSQL. Connection string kept as a secret. |
| **GitHub Actions** | Automation | Three workflows, below. |

### The three workflows

| Workflow | When | Does |
|---|---|---|
| `ci.yml` | Every push and PR | Runs the backend tests, TypeScript check and lint |
| `discovery.yml` | Every 6 hours | Runs the discovery pipeline against the live database |
| `keep-warm.yml` | On a schedule | Pings `/api/health` so the free Render backend doesn't fall asleep |

### Important environment variables

| Where | Variable | Purpose |
|---|---|---|
| Vercel | `NEXT_PUBLIC_API_URL` | Backend address |
| Vercel | `ZENKAI_ADMIN_TOKEN` | Service token for admin calls |
| Render | `DATABASE_URL` | Neon connection string |
| Render | `CORS_ORIGINS` | Allows the Vercel site to call the API |
| Render | `ENV=production` | Turns off auto table creation and the dev demo fallback |
| GitHub | `ZENK_AI_DB` secret | Database URL for the discovery workflow |

---

## 9. Walkthrough: what happens when someone clicks "Get started"

1. The browser submits the **GuestButton** form on the landing page.
2. Next.js runs the **`guestAction`** server action on Vercel.
3. `guestAction` calls **`POST /api/v1/auth/guest`** on the backend.
4. FastAPI's **auth router** calls **`auth_service.create_guest`**, which inserts
   a guest user, then **`start_session`** creates a token and stores its hash in
   Neon.
5. The backend returns the token. `guestAction` stores it in the httpOnly
   **`zenkai_session`** cookie and redirects to `/dashboard`.
6. **`proxy.ts`** sees the cookie and lets the request through.
7. The **private layout** calls `/auth/me` with the token, and the backend
   confirms who it is.
8. The **dashboard page** (a Server Component) fetches `/api/v1/dashboard`.
   The backend runs filters and matching, then returns JSON.
9. Next.js renders the HTML and sends it to the browser.

---

## 10. Running it locally

```
make install     # install backend and frontend dependencies
make seed        # create tables and load the catalogue
make backend     # API on http://localhost:8000  (docs at /docs)
make frontend    # site on http://localhost:3000
make test        # backend tests
make lint        # TypeScript check + ESLint
make discover    # run discovery once
```

Locally, with no login, the backend can fall back to the seeded demo student
(`ALLOW_DEMO_FALLBACK`). That's off in production.
