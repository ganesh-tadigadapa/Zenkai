"""Feed, detail and dashboard logic."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import CostType, DataOrigin, VerificationMethod, VerificationStatus
from app.models.interaction import SavedOpportunity
from app.models.opportunity import Opportunity, content_fingerprint
from app.models.organization import Organization
from app.models.user import User, UserPreferences
from app.repositories import opportunity_repository as repo
from app.repositories.opportunity_repository import OpportunityQuery
from app.services import destination_service
from app.services.matching import MatchResult, score_opportunity

CLOSING_SOON_DAYS = 14
NEW_TODAY_HOURS = 24


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)[:240] or "opportunity"


def unique_slug(db: Session, base: str) -> str:
    slug = slugify(base)
    candidate, n = slug, 2
    while db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.slug == candidate)):
        candidate = f"{slug}-{n}"
        n += 1
    return candidate


def days_left(opportunity: Opportunity, now: datetime | None = None) -> int | None:
    """Calendar days until the deadline.

    Deliberately date-based rather than a 24-hour subtraction: a deadline later
    today reads as 0 ("closing today") and tomorrow reads as 1, which is what a
    student expects. A raw timedelta would truncate 8d23h to "8 days left".
    """
    if opportunity.deadline is None or opportunity.is_rolling:
        return None
    now = now or datetime.now(timezone.utc)
    deadline = opportunity.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return (deadline.date() - now.date()).days


def saved_ids(db: Session, user_id: str | None) -> set[str]:
    if not user_id:
        return set()
    rows = db.scalars(
        select(SavedOpportunity.opportunity_id).where(SavedOpportunity.user_id == user_id)
    ).all()
    return set(rows)


def get_or_create_organization(db: Session, name: str, website: str | None = None) -> Organization:
    slug = slugify(name)
    org = db.scalars(select(Organization).where(Organization.slug == slug)).first()
    if org:
        return org
    org = Organization(name=name, slug=slug, website=website)
    db.add(org)
    db.flush()
    return org


def decorate(
    opportunity: Opportunity,
    *,
    prefs: UserPreferences | None,
    saved: set[str],
    now: datetime | None = None,
) -> dict:
    """Attach the per-user fields the ORM row cannot know about."""
    match: MatchResult | None = score_opportunity(opportunity, prefs, now) if prefs else None
    return {
        "days_left": days_left(opportunity, now),
        "destination": destination_service.as_dict(opportunity),
        "is_saved": opportunity.id in saved,
        "match": None
        if match is None
        else {
            "score": match.score,
            "reasons": [r.__dict__ for r in match.reasons],
        },
    }


def list_opportunities(
    db: Session, q: OpportunityQuery, user: User | None = None
) -> tuple[list[tuple[Opportunity, dict]], int]:
    rows, total = repo.search(db, q)
    prefs = user.preferences if user else None
    saved = saved_ids(db, user.id if user else None)
    now = datetime.now(timezone.utc)

    decorated = [(row, decorate(row, prefs=prefs, saved=saved, now=now)) for row in rows]

    if q.sort == "relevance":
        decorated.sort(
            key=lambda pair: (
                -(pair[1]["match"]["score"] if pair[1]["match"] else 0),
                pair[0].deadline or datetime.max.replace(tzinfo=timezone.utc),
            )
        )
        decorated = decorated[q.offset : q.offset + q.limit]

    return decorated, total


def get_detail(db: Session, identifier: str, user: User | None = None) -> tuple[Opportunity, dict] | None:
    row = repo.get_by_id_or_slug(db, identifier)
    if row is None:
        return None
    prefs = user.preferences if user else None
    return row, decorate(row, prefs=prefs, saved=saved_ids(db, user.id if user else None))


# --- Dashboard shelves -------------------------------------------------------

PUBLIC_STATUSES = [
    VerificationStatus.CURATED.value,
    VerificationStatus.SOURCE_CHECKED.value,
    VerificationStatus.NEEDS_REVIEW.value,
]


def _public(q: OpportunityQuery) -> OpportunityQuery:
    q.statuses = list(PUBLIC_STATUSES)
    return q


def recommended(db: Session, user: User | None, limit: int = 6):
    q = _public(OpportunityQuery(sort="relevance", limit=limit))
    items, _ = list_opportunities(db, q, user)
    return items[:limit]


def new_today(db: Session, user: User | None, limit: int = 6):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=NEW_TODAY_HOURS)
    q = _public(OpportunityQuery(sort="newest", limit=200))
    rows, _ = repo.search(db, q)
    fresh = [r for r in rows if _aware(r.discovered_at) >= cutoff][:limit]
    if not fresh:  # seeded databases can be older than 24h — fall back to newest
        fresh = rows[:limit]
    prefs = user.preferences if user else None
    saved = saved_ids(db, user.id if user else None)
    return [(r, decorate(r, prefs=prefs, saved=saved)) for r in fresh]


def closing_soon(db: Session, user: User | None, limit: int = 6, within_days: int = CLOSING_SOON_DAYS):
    q = _public(OpportunityQuery(sort="deadline", limit=limit, deadline_within_days=within_days))
    items, _ = list_opportunities(db, q, user)
    return items


def recently_updated(db: Session, user: User | None, limit: int = 6):
    q = _public(OpportunityQuery(sort="updated", limit=limit))
    items, _ = list_opportunities(db, q, user)
    return items


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def stats(db: Session, user: User | None) -> dict:
    now = datetime.now(timezone.utc)
    today = repo.start_of_day(now)
    live = (
        Opportunity.verification_status.in_(PUBLIC_STATUSES),
        or_(Opportunity.deadline.is_(None), Opportunity.deadline >= today),
    )
    total = db.scalar(select(func.count()).select_from(Opportunity).where(*live)) or 0
    new_count = (
        db.scalar(
            select(func.count())
            .select_from(Opportunity)
            .where(*live, Opportunity.discovered_at >= now - timedelta(hours=NEW_TODAY_HOURS))
        )
        or 0
    )
    closing = (
        db.scalar(
            select(func.count())
            .select_from(Opportunity)
            .where(
                *live,
                Opportunity.deadline.is_not(None),
                Opportunity.deadline <= now + timedelta(days=CLOSING_SOON_DAYS),
            )
        )
        or 0
    )
    saved_count = (
        db.scalar(
            select(func.count())
            .select_from(SavedOpportunity)
            .where(SavedOpportunity.user_id == user.id)
        )
        if user
        else 0
    ) or 0

    matched = 0
    if user and user.preferences:
        rows, _ = repo.search(db, _public(OpportunityQuery(limit=500)))
        matched = sum(1 for r in rows if score_opportunity(r, user.preferences, now).score >= 60)

    return {
        "total": int(total),
        "new_today": int(new_count),
        "closing_soon": int(closing),
        "saved": int(saved_count),
        "matched": matched,
    }


def create_opportunity(db: Session, payload, *, source_id: str | None = None) -> Opportunity:
    """Create one opportunity, rejecting exact duplicates via the content hash."""
    org = get_or_create_organization(db, payload.organization_name, payload.organization_website)
    fingerprint = content_fingerprint(payload.title, org.name, str(payload.application_url))
    existing = db.scalars(
        select(Opportunity).where(Opportunity.content_hash == fingerprint)
    ).first()
    if existing:
        return existing

    row = Opportunity(
        title=payload.title,
        slug=unique_slug(db, payload.title),
        organization_id=org.id,
        source_id=source_id or getattr(payload, "source_id", None),
        category=payload.category.value,
        secondary_categories=[c.value for c in payload.secondary_categories],
        opportunity_type=payload.opportunity_type.value,
        summary=payload.summary,
        description=payload.description,
        eligibility=payload.eligibility,
        who_can_apply=payload.who_can_apply,
        location=payload.location,
        is_remote=payload.is_remote,
        cost_type=payload.cost_type.value,
        cost_amount=payload.cost_amount,
        currency=payload.currency,
        deadline=payload.deadline,
        is_rolling=payload.is_rolling,
        deadline_is_estimated=getattr(payload, "deadline_is_estimated", False),
        application_url=str(payload.application_url),
        source_url=str(payload.source_url),
        direct_destination_url=(
            str(payload.direct_destination_url) if payload.direct_destination_url else None
        ),
        destination_action=(
            payload.destination_action.value if payload.destination_action else None
        ),
        skills=payload.skills,
        tags=payload.tags,
        benefits=payload.benefits,
        verification_status=getattr(
            payload, "verification_status", VerificationStatus.NEEDS_REVIEW
        ).value,
        verification_method=getattr(
            payload, "verification_method", VerificationMethod.NONE
        ).value,
        published_at=getattr(payload, "published_at", None),
        data_origin=getattr(payload, "data_origin", DataOrigin.MANUAL).value,
        confidence=getattr(payload, "confidence", 0.5),
        content_hash=fingerprint,
        last_checked_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    return row


def expire_passed_deadlines(db: Session, now: datetime | None = None) -> int:
    """Mark opportunities whose deadline has passed as EXPIRED. Returns the count."""
    now = now or datetime.now(timezone.utc)
    rows = db.scalars(
        select(Opportunity).where(
            Opportunity.deadline.is_not(None),
            Opportunity.deadline < now,
            Opportunity.is_rolling.is_(False),
            Opportunity.verification_status != VerificationStatus.EXPIRED.value,
            Opportunity.verification_status != VerificationStatus.REJECTED.value,
        )
    ).all()
    for row in rows:
        row.verification_status = VerificationStatus.EXPIRED.value
        row.last_checked_at = now
    db.flush()
    return len(rows)


__all__ = [
    "CostType",
    "OpportunityQuery",
    "closing_soon",
    "create_opportunity",
    "days_left",
    "decorate",
    "expire_passed_deadlines",
    "get_detail",
    "list_opportunities",
    "new_today",
    "recently_updated",
    "recommended",
    "slugify",
    "stats",
    "unique_slug",
]
