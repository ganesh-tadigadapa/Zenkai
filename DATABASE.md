# Database

PostgreSQL is the target, and the full stack has been run and verified against
PostgreSQL 16. The schema stays portable to SQLite so the project also runs with
no database server at all — see [Portability](#portability).

```
organizations ──< opportunities >── sources
                       │
        ┌──────────────┼──────────────┐
        │              │              │
saved_opportunities  verification_reviews  notifications
        │                                      │
      users ──── user_preferences ─────────────┘
```

---

## Tables

### `opportunities`

The central table. One row per discoverable opportunity.

| Column | Type | Notes |
|---|---|---|
| `id` | varchar(36) PK | UUID4 |
| `slug` | varchar(260) | Unique, indexed. Human-readable URL |
| `title` | varchar(240) | |
| `organization_id` | FK → organizations | `ON DELETE RESTRICT` — never orphan a record |
| `source_id` | FK → sources, nullable | `ON DELETE SET NULL` |
| `category` | varchar(32) | Indexed. One of the six product categories |
| `secondary_categories` | json | Cross-cutting, rarely queried |
| `opportunity_type` | varchar(32) | Indexed. Finer-grained than category |
| `summary` | varchar(400) | Card text |
| `description` | text | Detail page body |
| `eligibility` | text, nullable | Prose |
| `who_can_apply` | json | Short chips |
| `location` | varchar(160) | Free text; `Global` when unbounded |
| `is_remote` | boolean | Indexed |
| `cost_type` | varchar(32) | Indexed. free / free_for_students / discounted / paid |
| `cost_amount`, `currency` | float, varchar(8) | Only meaningful when `cost_type = paid` |
| `deadline` | timestamptz, nullable | Indexed |
| `is_rolling` | boolean | True ⇒ no deadline to track |
| `deadline_is_estimated` | boolean | See [Estimated deadlines](#estimated-deadlines) |
| `application_url` | varchar(600) | Legacy "where the student goes"; kept because `content_hash` is derived from it |
| `source_url` | varchar(600) | The authoritative provider page |
| `direct_destination_url` | varchar(600), nullable | The exact page where a student can start, enrol, register or apply. NULL when that page could not be established |
| `destination_action` | varchar(32), nullable | Overrides the action derived from `opportunity_type` |
| `last_url_checked_at` | timestamptz, nullable | When the URLs were last fetched |
| `url_check_status` | varchar(16) | `ok` / `blocked` / `unreachable` / `broken` / `unchecked` |
| `skills`, `tags`, `benefits` | json | String arrays |
| `verification_status` | varchar(24) | Indexed. See below |
| `verification_method` | varchar(24) | How that status was reached: none / curation / human_review / source_fetch / automated |
| `data_origin` | varchar(16) | Indexed. seed / ingested / manual |
| `confidence` | float | 0–1, from the extractor |
| `verified_at`, `verified_by` | timestamptz, varchar(160) | Who checked, and when |
| `last_checked_at` | timestamptz | Freshness indicator shown on every card |
| `discovered_at` | timestamptz | Indexed. Drives "new today" |
| `published_at` | timestamptz, nullable | When the source published it, as distinct from when we recorded it. Null until a source reports it |
| `content_hash` | varchar(64) | **Unique.** Deduplication key |
| `created_at`, `updated_at` | timestamptz | `updated_at` auto-updates |

**Indexes**

- Unique on `slug` and `content_hash`
- Single-column on `category`, `opportunity_type`, `cost_type`, `is_remote`,
  `deadline`, `verification_status`, `data_origin`, `discovered_at`,
  `organization_id`
- Composite `ix_opportunities_feed` on `(verification_status, category, deadline)`
  — matches the default feed query's leading predicates

#### Why `category` is a column, not a join table

A brief called for `categories` and `opportunity_categories` tables. The six
categories are a fixed product commitment rather than user-managed data, so a
join table would add a join to every feed query and make a seventh category
something that could appear through an admin form rather than a deliberate code
change. Cross-cutting facets go in `tags`, which is what they actually are.

#### `content_hash`

`sha256(lower(title) | lower(organization) | url-without-query)`.

The unique constraint means the database rejects exact duplicates regardless of
which code path inserts them. Fuzzy near-duplicates are handled a layer up in
`DeduplicationService`.

#### Verification status

Deliberately modest. The vocabulary exists so the interface can never imply a
freshness the system has not earned.

| Value | Meaning |
|---|---|
| `curated` | A person wrote the record from the official page. Nothing re-checks it afterwards |
| `source_checked` | The official source was actually fetched, or a reviewer confirmed it in the queue |
| `needs_review` | Not confirmed by anyone. Visible to students, labelled as such |
| `expired` | Closed, or the deadline has passed |
| `rejected` | A reviewer rejected it. **Never shown to students** |

No seed record carries `source_checked`, and `tests/test_seed_integrity.py`
asserts it: nothing fetches anything yet, so nothing may claim it did.

`verification_status`, `verification_method` and `data_origin` are three
independent facts — *how confident*, *how established*, and *where from*.
Collapsing them would make "curated by hand, not re-checked" impossible to say
without implying a live check.

#### The two URLs

A record has an authoritative page and, ideally, an actionable one.

* `source_url` is the provider's own page — always present.
* `direct_destination_url` is where the student can act. It is **NULL whenever
  that page could not be established from an official source**, and the
  interface then falls back to `source_url` with a button that says "Visit
  official source" rather than dressing a homepage up as an enrolment link.

`destination_type` is *derived*, never stored: a record either has a direct
destination or it does not. Deriving it removes any chance of the stored value
disagreeing with the URLs beside it.

Button wording comes from `opportunity_type` rather than a parallel
credential-type column, for the same reason — a record typed as an exam cannot
end up saying "Start course". `destination_action` exists only to override that
default for the rare record whose destination does something its type does not
imply.

`url_check_status` distinguishes `blocked` from `broken`. Several providers
reject non-browser clients with 403; that is not a dead link, and conflating
the two would send reviewers chasing pages that work perfectly for a student.

#### Deadlines

`deadline` is null unless the official source publishes a standing date. Real
programmes often run on an annual cycle whose dates are announced each year;
inferring a date from that cycle would be inventing one, so the catalogue does
not, and the interface reads "Deadline not listed".

`deadline_is_estimated` remains on the model for a future extractor that reports
its own confidence in a parsed date. Nothing sets it today.

---

### `organizations`

`id`, `name`, `slug` (unique), `website`, `logo_url`, `description`.

Created on demand by `get_or_create_organization`, keyed on the slug, so
ingestion never produces duplicate organisations from spelling variants.

---

### `sources`

The registry the ingestion pipeline reads from.

| Column | Notes |
|---|---|
| `name`, `url` | |
| `source_type` | official_api / rss / atom / web / social_signal / manual |
| `category` | Optional hint about what this source yields |
| `trust_level` | 1–5. Feeds into the verification confidence score |
| `active` | Inactive sources are never fetched |
| `check_frequency_minutes` | Drives `scheduler.is_due` |
| `last_checked_at` | |
| `robots_allowed` | **False ⇒ never fetched.** Enforced in `SourceConnector.is_permitted` |
| `access_notes` | Why, in prose, for the next engineer |

A source that prohibits automated access is stored rather than omitted, so the
prohibition is a fact in the system instead of tribal knowledge.

---

### `users`, `user_preferences`

`users` holds `email` (unique), `name`, `is_admin`. Passwords are deliberately
absent — this build has no authentication.

`user_preferences` is one row per user, keyed by `user_id` as the primary key:
`degree`, `field_of_study`, `year`, `country`, `location`,
`remote_preference`, and `skills` / `interests` / `preferred_categories` as JSON
arrays. All of it is input to `services/matching.py` and nothing else.

---

### `saved_opportunities`

Composite primary key `(user_id, opportunity_id)`, which makes saving naturally
idempotent, plus `notes` and `created_at`. Both foreign keys cascade on delete.

---

### `verification_reviews`

Append-only audit log. `opportunity_id`, `reviewer`, `action`
(approve/reject/edit), `previous_status`, `new_status`, `notes`, and `changes`
— a JSON field-level diff for edits.

Rows are never updated or deleted. A record's current verification state can
always be traced back through this table.

---

### `notifications`

`user_id`, `opportunity_id`, `channel`, `status` (pending/sent/failed),
`title`, `body`, `sent_at`. The model and service exist; no channel delivers
yet.

---

---

## The discovery engine's tables

### `credential_details`

Certification-specific facts, one row per opportunity, keyed by
`opportunity_id`. A detail table rather than more columns on `opportunities`,
so the six categories can share one pipeline while differing in schema.

| Column | Notes |
|---|---|
| `credential_type` | 14 values. A course completion certificate is not a professional certification |
| `specializations` | JSON list from a 35-member taxonomy. Drives search and matching |
| `issuer` | The awarding body, where it differs from the listing organisation |
| `exam_code` | Indexed. "AZ-900" — a strong dedup signal and what students search for |
| `assessment_type` | 10 values |
| `proctored_status` | `yes` / `no` / `optional` / `unknown` |
| `delivery_mode`, `experience_level` | |
| `duration_hours`, `validity_months` | NULL means unstated, not zero and not forever |
| `available_countries` | Empty means unstated, which is not the same as worldwide |

**Every field defaults to UNKNOWN.** A source that does not mention proctoring
has not said there is none. `tests/test_intelligence_engine.py` asserts that
UNKNOWN is never written as NO.

### `source_checks`

One row per attempt to read a source, **including the failures**. Records
counts of documents retrieved, candidates extracted, and what each sighting
did. A source with no checks reports "Not monitored yet." rather than an
invented timestamp.

### `raw_source_documents`

What a source actually returned, kept before anything interprets it, with a
content digest so an unchanged page is cheap to recognise. Never holds
credentials: request headers, cookies and authorization values are not stored,
and credential-shaped metadata keys are stripped on write.

### `opportunity_provenance`

Links a published opportunity to the evidence behind it — many-to-one, because
several sources may describe the same thing and merging must not destroy the
record of who said what. Carries the change kind and a field-level diff, so a
reviewer can see that a cost moved and what it moved from.

### `sources` — access versus authority

Two independent properties:

* `robots_allowed`, `active` — whether the source may be **read**.
* `authority` — whether its word can support `SOURCE_CHECKED`. Only the five
  tiers in `AUTHORITATIVE_SOURCES` can; a platform listing is a discovery
  signal, not evidence of cost or eligibility.

`discovery_method` defaults to UNKNOWN. No source is assumed to offer an API
because one would be convenient.

---

## Portability

The schema targets PostgreSQL but runs unchanged on SQLite:

| Choice | Reason |
|---|---|
| `JSON`, not `JSONB` | SQLite has no JSONB |
| String-backed enums, not native `ENUM` | SQLite has no enum type; also avoids a migration for every new value |
| `UTCDateTime` `TypeDecorator` | SQLite drops timezone offsets; this normalises both directions so application code always sees aware UTC |
| `LIKE` over `cast(json AS text)` for array search | Portable, at the cost of scaling |

### What to change for production PostgreSQL

1. **Search.** Replace the `LIKE` predicates in
   `opportunity_repository.apply_filters` with a `tsvector` column over title,
   summary, description and organisation, plus a GIN index. The current approach
   is correct but will not hold past roughly 10⁴ rows.
2. **JSON columns.** Move `skills`, `tags` and `benefits` to `JSONB` with GIN
   indexes so skill filtering stops being a substring scan.
3. **Migrations.** `create_all()` runs at startup in development only. Add
   Alembic before there is a second environment; the models are already
   structured for autogenerate.
4. **Connection pooling.** `pool_pre_ping` is on for non-SQLite URLs; size the
   pool for the deployment.

---

## Seeding

```bash
python -m app.seed.run            # idempotent — matches on content_hash
python -m app.seed.run --reset    # drop everything first
```

Loads 54 curated opportunities, 10 sources, a demo student and a reviewer
account. Re-running without `--reset` is safe.

Every seeded opportunity is stored with `data_origin = 'seed'`. Records marked
`curated` were written from their official URL during curation and carry
`verified_by = 'zenkai-curation'` with `verification_method = 'curation'`, so the
distinction from a live check is visible in the data itself, not only in the UI.
