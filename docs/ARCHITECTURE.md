# Architecture

## The shape of the problem

Zenkai is a **trust pipeline**, not a scraper with a UI. Anyone can collect
links; the hard part is knowing whether a record is accurate today, and being
honest with the student when it might not be.

Every design decision below follows from that.

```
SOURCE ─▶ DISCOVERY ─▶ INGESTION ─▶ EXTRACTION ─▶ DEDUPLICATION
                                                        │
        DATABASE ◀─ HUMAN REVIEW ◀─ VERIFICATION ◀──────┘
            │
            └─▶ PERSONALISATION ─▶ NOTIFICATION
```

Stages implemented in this build: everything except the network fetch inside
each connector, real LLM extraction, and notification delivery. Those three have
interfaces and tests but no live implementation, which is stated on the product
itself rather than left for the reader to discover.

---

## Repository layout

```
backend/
  app/
    core/           config and database wiring
    models/         SQLAlchemy models + shared enums
    schemas/        Pydantic request/response contracts
    repositories/   query construction (filtering, search, sorting)
    services/       business logic (feed, matching, saving, review)
    api/v1/routers/ HTTP layer — thin, no logic
    ingestion/      connectors, extraction, dedup, verification, pipeline
    ai/             provider-agnostic AI contracts + heuristic stub
    notifications/  notification model and channel interface
    seed/           curated catalogue and the seeder
  tests/            86 tests

frontend/
  src/
    app/
      (app)/        signed-in shell: dashboard, feed, detail, saved, …
      page.tsx      landing page
    components/     ui primitives, opportunity, filters, admin, layout
    lib/            typed API client, server actions, formatting
```

---

## Backend

### Layering

`router → service → repository → model`

Routers only parse and serialise. Services hold decisions. Repositories hold
SQLAlchemy. This matters most in `opportunity_repository.apply_filters`, which
is the single definition of "what a student may see" — the feed, the deadline
view and the dashboard shelves all go through it, so they cannot drift apart.

The layering is applied where it earns its place. There is no repository for
users or saved items, because those are single-row lookups and an extra file
would add indirection without adding anything.

### Categories are an enum, not a table

The six categories are a product commitment, not user data. Making them an enum
column means every feed query is one indexed scan with no join, and adding a
seventh category is a deliberate code change rather than something that happens
by accident through an admin form. Cross-cutting facets live in `tags`.

### Timezone handling

SQLite silently drops timezone offsets while PostgreSQL preserves them, so the
same code produced aware datetimes on one backend and naive ones on the other.
Rather than defend against that at every call site, `models/base.UTCDateTime` is
a `TypeDecorator` that normalises both directions. Application code can assume
every datetime it receives is UTC-aware.

### Deadlines are dates, not instants

`days_left` counts calendar days, and the feed filter compares against the start
of the current day. An opportunity closing at 09:00 today stays visible all day,
and a deadline nine days out reads as "9 days left" rather than 8. Both rules
live in one place each (`opportunity_service.days_left`,
`opportunity_repository.start_of_day`) because they must agree — when they
disagreed, records closing earlier the same day vanished from the feed while
still being counted in the dashboard metrics.

### Verification, method and origin

Three independent columns, deliberately:

- `verification_status` — how much confidence may be expressed: `curated`,
  `source_checked`, `needs_review`, `expired`, `rejected`.
- `verification_method` — how that status was reached: `curation`,
  `human_review`, `source_fetch`, `automated`, `none`.
- `data_origin` — where the record came from: `seed`, `ingested`, `manual`.

The split exists so the interface can say "a person wrote this from the official
page, and nothing has re-checked it since" — which is the truth for today's
catalogue — instead of a green tick that implies a live check. `source_checked`
is unreachable by any current code path except a reviewer approving in the
queue, and a test asserts no seeded record claims it.

`verification_reviews` is append-only. Every approve, reject and edit writes a
row with the previous status, the new status, the reviewer and a field-level
diff, so a record's current state can always be explained.

### Deduplication

Two layers. `content_hash` is a SHA-256 of normalised title, organisation and
application URL with the query string stripped, and carries a unique constraint
— the database itself refuses exact duplicates. Above it, `DeduplicationService`
compares token overlap on titles within the same organisation to catch re-posts
that differ only in wording.

### Ingestion compliance

`SourceConnector.is_permitted` runs before any network call and refuses to fetch
a source that is inactive or has `robots_allowed = false`. Sources that prohibit
automated access are still registered — LinkedIn is in the seed data with
`robots_allowed = false` and an explanatory note — specifically so the system
holds an explicit record of what it must never touch, rather than relying on
that knowledge living only in someone's head.

Automated verification cannot promote a record on its own. `AUTO_APPROVE_CONFIDENCE`
is 0.95 and the heuristic extractor caps its own confidence at 0.65, so every
stub-extracted record lands in the human queue. A test asserts this rather than
leaving it to convention.

### The discovery engine's stages

The pipeline the brief describes maps onto modules that already existed, plus
four that were missing:

| Stage | Where it lives | State |
|---|---|---|
| Source registry | `models/source.py` | Authority taxonomy, discovery method, cadence, failure counters |
| Discovery | `ingestion/connectors/` | Contract and compliance gate built; no network fetch |
| Raw source data | `models/provenance.py` | Persisted before anything interprets it |
| Extraction | `ingestion/extraction.py` + `ai/` | Heuristic stub behind a provider interface |
| Normalisation | `models/credential.py` | Certification vertical built out |
| Deduplication | `ingestion/deduplication.py` | Fingerprint plus token overlap |
| Verification | `ingestion/verification.py` | Plausibility checks, routes to review |
| Monitoring | `ingestion/monitoring.py` | Change detection and the mass-deletion guard |

Two decisions are worth stating because they are easy to get wrong.

**Access and authority are different questions.** `robots_allowed` and `active`
decide whether a source may be *read*. `authority` decides whether its word can
support a record being published as `SOURCE_CHECKED`. A platform listing is
useful for discovering that something exists; it is not evidence of what it
costs or who may apply. Only the five authority tiers in
`AUTHORITATIVE_SOURCES` can support that claim.

**Raw evidence is kept.** `raw_source_documents` holds what a source returned,
before extraction touches it. Extraction and normalisation will improve;
keeping the raw documents means those improvements can be re-run over what we
already have rather than asking providers for the same pages again. It is also
the audit trail — every published record traces back through
`opportunity_provenance` to the document it came from. Deduplication adds a
provenance row rather than discarding a second sighting, so several sources
agreeing does not destroy the record of who said what.

Credential-shaped metadata keys are stripped before storage, with a test
asserting it: no headers, cookies or authorization values reach the table.

### Category-specific schemas, one pipeline

`credential_details` is a detail table keyed to `opportunities`, not more
columns on the shared row. That is what lets the six categories share one
discovery pipeline while differing in schema — internships and scholarships can
add their own detail tables without widening the row every category reads.

Every credential field defaults to UNKNOWN, and UNKNOWN is a real answer. A
source that does not mention proctoring has not told us there is none, and
`ProctoredStatus.UNKNOWN` is never collapsed to `NO`. The interface shows
"Not stated by the provider" rather than hiding the field, because a gap is
information: it tells a student something has not been established.

### AI provider boundary

`ai/base.py` defines six operations (extract, classify, extract_deadline,
extract_eligibility, summarize, confidence) as a `Protocol`. `ai/stub_client.py`
implements them with regular expressions and keyword heuristics — deterministic,
dependency-free, and useful in tests. Swapping in a real model means writing one
class and registering it in `get_ai_client()`; no pipeline code changes.

### Authentication

Out of scope for this build, and honestly so. A request may carry `X-User-Id`;
otherwise it resolves to the seeded demo student. Admin routes require a shared
`X-Admin-Token`. This is not production authentication and the code says so at
the definition site.

---

## Frontend

### The entrance sequence

`components/intro/` holds the 0→100% intro. Its storyboard is data
(`script.ts`), so beats can be reordered or retimed without touching animation
code. Three constraints shape the implementation:

- **It renders nothing on the server.** Whether to play is read through
  `useSyncExternalStore` with a server snapshot of `false`, so returning
  visitors never get a flash of an overlay that is about to disappear.
- **The counter is driven by elapsed time**, not by frame count, so a dropped
  frame cannot desynchronise the number from the beats or stretch the sequence.
- **`prefers-reduced-motion` skips it outright.** Someone who asked for less
  motion did not ask for a faster cinematic.

### Server-first rendering

Pages are React Server Components that call the API directly. Only five
components are client components, each for a specific reason: optimistic
save state, filter controls that write to the URL, the search field's keyboard
shortcut, the review actions' inline confirmation, and the theme toggle.

There is no client-side data fetching, no SWR/React Query, and no global store.

### Mutations are server actions

Every write goes through `lib/actions.ts`. This keeps the admin token on the
server — verified by grepping the built client bundle — and lets each action
revalidate exactly the paths its change invalidates.

### Caching

Most API responses embed per-user fields (`is_saved`, `match`), and Next's data
cache is shared across requests, so caching those would serve one student's
state to another. User-scoped requests are therefore uncached by default; only
genuinely shared data — category counts, facet counts, the source registry —
opts into a revalidation window.

### Filters live in the URL

Every filter, sort and page is a search param. Views are shareable, restorable
on refresh, and back/forward works. `ActiveFilters` renders a removable chip per
applied filter so nothing filters silently.

### Design system

Two layers of CSS custom properties in `globals.css`: raw values per theme, then
a Tailwind v4 `@theme inline` block mapping them to utility names. Components
only ever use the semantic names (`bg-surface`, `text-muted`), so both themes
stay in step by construction.

One accent colour carries the brand. Green, amber and rose are reserved
exclusively for verification state and deadline urgency, so a colour never means
two things at once.

The theme toggle holds no React state — the glyph is chosen by the same CSS
rules that set the palette, which removes the mount flash a state-based toggle
needs and keeps server and client markup identical.

---

## Trade-offs taken

| Decision | Why | Cost |
|---|---|---|
| SQLite default | Runs with zero setup; portable schema | Not production-grade; no JSONB or GIN indexes |
| `LIKE` search over JSON-cast columns | Portable across both backends | Will not scale past ~10⁴ rows — see DATABASE.md |
| Rule-based matching | Explainable, testable, honest | Will not surface non-obvious matches |
| Header-based identity | Keeps focus on the product surface | Not usable by real users |
| Connectors unimplemented | A half-working crawler is worse than none | Catalogue is manual until one is written |
| `create_all()` in development | No migration step while the schema moves | Needs Alembic before a second environment |
| Credentials in a detail table | Six categories share one pipeline, differ in schema | A join on credential-filtered queries |
| Raw documents stored in full | Re-extraction without re-fetching; real audit trail | Table grows with every check |
