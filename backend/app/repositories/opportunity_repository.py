"""Query construction for the opportunity feed.

All filtering, search and sorting lives here so the service layer stays free of
SQLAlchemy details and the same predicates are reused by the feed, the deadline
view and the admin queue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, Text, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.credential import CredentialDetail
from app.models.enums import CostType, VerificationStatus
from app.models.opportunity import Opportunity
from app.models.organization import Organization

SORTABLE = {"deadline", "newest", "updated", "relevance", "title"}


@dataclass
class OpportunityQuery:
    search: str | None = None
    categories: list[str] = field(default_factory=list)
    types: list[str] = field(default_factory=list)
    cost: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    remote: bool | None = None
    location: str | None = None
    free_only: bool = False
    verified_only: bool = False
    statuses: list[str] = field(default_factory=list)
    # Credential facets. Each filters on the certification detail table, so a
    # record with no credential row is excluded rather than assumed to match.
    credential_types: list[str] = field(default_factory=list)
    specializations: list[str] = field(default_factory=list)
    assessment_types: list[str] = field(default_factory=list)
    proctored: list[str] = field(default_factory=list)
    delivery_modes: list[str] = field(default_factory=list)
    experience_levels: list[str] = field(default_factory=list)
    issuers: list[str] = field(default_factory=list)
    deadline_within_days: int | None = None
    include_expired: bool = False
    sort: str = "deadline"
    limit: int = 24
    offset: int = 0


def _base_select() -> Select:
    return select(Opportunity).options(
        joinedload(Opportunity.organization),
        joinedload(Opportunity.source),
        joinedload(Opportunity.credential),
    )


def start_of_day(moment: datetime) -> datetime:
    """A deadline is a date, not an instant.

    Something closing "today" stays visible for the whole of today, which matches
    how ``days_left`` counts. Comparing against the current instant would hide an
    opportunity at 14:00 whose stored deadline is 09:00 the same day.
    """
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def apply_filters(stmt: Select, q: OpportunityQuery, now: datetime | None = None) -> Select:
    now = now or datetime.now(timezone.utc)
    today = start_of_day(now)

    if q.statuses:
        stmt = stmt.where(Opportunity.verification_status.in_(q.statuses))
    else:
        # The public feed never shows rejected records.
        stmt = stmt.where(Opportunity.verification_status != VerificationStatus.REJECTED.value)

    # Applied independently of `statuses`: callers pass the set of statuses the
    # surface may show, and this narrows that further on request. "Checked"
    # covers both curated-by-hand and source-checked records — the two states in
    # which a human has looked at the official page.
    if q.verified_only:
        stmt = stmt.where(
            Opportunity.verification_status.in_(
                [VerificationStatus.CURATED.value, VerificationStatus.SOURCE_CHECKED.value]
            )
        )

    if not q.include_expired:
        stmt = stmt.where(
            Opportunity.verification_status != VerificationStatus.EXPIRED.value,
            or_(
                Opportunity.deadline.is_(None),
                Opportunity.is_rolling.is_(True),
                Opportunity.deadline >= today,
            ),
        )

    if q.categories:
        stmt = stmt.where(Opportunity.category.in_(q.categories))
    if q.types:
        stmt = stmt.where(Opportunity.opportunity_type.in_(q.types))
    if q.cost:
        stmt = stmt.where(Opportunity.cost_type.in_(q.cost))
    if q.free_only:
        stmt = stmt.where(
            Opportunity.cost_type.in_([CostType.FREE.value, CostType.FREE_FOR_STUDENTS.value])
        )
    if q.remote is not None:
        stmt = stmt.where(Opportunity.is_remote.is_(q.remote))
    if q.location:
        stmt = stmt.where(Opportunity.location.ilike(f"%{q.location}%"))
    if q.organizations:
        stmt = stmt.join(Organization, Opportunity.organization_id == Organization.id).where(
            or_(
                Organization.slug.in_(q.organizations),
                Organization.name.in_(q.organizations),
            )
        )
    if q.deadline_within_days is not None:
        horizon = now + timedelta(days=q.deadline_within_days)
        stmt = stmt.where(Opportunity.deadline.is_not(None), Opportunity.deadline <= horizon)

    # Credential facets, joined once and only when something asks for them.
    credential_filters = (
        q.credential_types
        or q.specializations
        or q.assessment_types
        or q.proctored
        or q.delivery_modes
        or q.experience_levels
        or q.issuers
    )
    if credential_filters:
        stmt = stmt.join(
            CredentialDetail, CredentialDetail.opportunity_id == Opportunity.id
        )
        if q.credential_types:
            stmt = stmt.where(CredentialDetail.credential_type.in_(q.credential_types))
        if q.assessment_types:
            stmt = stmt.where(CredentialDetail.assessment_type.in_(q.assessment_types))
        if q.proctored:
            stmt = stmt.where(CredentialDetail.proctored_status.in_(q.proctored))
        if q.delivery_modes:
            stmt = stmt.where(CredentialDetail.delivery_mode.in_(q.delivery_modes))
        if q.experience_levels:
            stmt = stmt.where(CredentialDetail.experience_level.in_(q.experience_levels))
        if q.issuers:
            stmt = stmt.where(CredentialDetail.issuer.in_(q.issuers))
        if q.specializations:
            stmt = stmt.where(
                or_(
                    *[
                        func.lower(func.cast(CredentialDetail.specializations, Text)).like(
                            f"%{value.lower()}%"
                        )
                        for value in q.specializations
                    ]
                )
            )

    if q.search:
        term = f"%{q.search.strip()}%"
        # Credential fields are part of search: students look for "AZ-900" and
        # "kubernetes", which live on the detail table, not the shared row.
        stmt = stmt.outerjoin(
            Organization, Opportunity.organization_id == Organization.id
        )
        if not credential_filters:
            stmt = stmt.outerjoin(
                CredentialDetail, CredentialDetail.opportunity_id == Opportunity.id
            )
        stmt = stmt.where(
            or_(
                Opportunity.title.ilike(term),
                Opportunity.summary.ilike(term),
                Opportunity.description.ilike(term),
                Opportunity.category.ilike(term),
                Opportunity.opportunity_type.ilike(term),
                Opportunity.location.ilike(term),
                CredentialDetail.exam_code.ilike(term),
                CredentialDetail.issuer.ilike(term),
                CredentialDetail.credential_type.ilike(term),
                func.lower(func.cast(CredentialDetail.specializations, Text)).like(term.lower()),
                # skills/tags are JSON arrays; casting to text keeps this portable
                # across SQLite and PostgreSQL. Swap for a GIN index in production.
                func.lower(func.cast(Opportunity.skills, Text)).like(term.lower()),
                func.lower(func.cast(Opportunity.tags, Text)).like(term.lower()),
                Organization.name.ilike(term),
            )
        )

    if q.skills:
        skill_clauses = [
            func.lower(func.cast(Opportunity.skills, Text)).like(f"%{s.lower()}%")
            for s in q.skills
        ]
        stmt = stmt.where(or_(*skill_clauses))

    return stmt


def apply_sort(stmt: Select, sort: str) -> Select:
    if sort == "newest":
        return stmt.order_by(Opportunity.discovered_at.desc())
    if sort == "updated":
        return stmt.order_by(Opportunity.updated_at.desc())
    if sort == "title":
        return stmt.order_by(Opportunity.title.asc())
    # "deadline" (default) and "relevance" both start from soonest-closing;
    # relevance is re-ranked in Python once match scores are known.
    return stmt.order_by(
        Opportunity.deadline.is_(None), Opportunity.deadline.asc(), Opportunity.discovered_at.desc()
    )


def search(db: Session, q: OpportunityQuery) -> tuple[list[Opportunity], int]:
    stmt = apply_filters(_base_select(), q)
    total = db.scalar(
        select(func.count()).select_from(apply_filters(select(Opportunity), q).subquery())
    )
    stmt = apply_sort(stmt, q.sort if q.sort in SORTABLE else "deadline")
    # "relevance" needs the whole candidate set in memory to re-rank by score.
    if q.sort != "relevance":
        stmt = stmt.limit(q.limit).offset(q.offset)
    rows = list(db.scalars(stmt).unique().all())
    return rows, int(total or 0)


def get_by_id_or_slug(db: Session, identifier: str) -> Opportunity | None:
    stmt = _base_select().where(
        or_(Opportunity.id == identifier, Opportunity.slug == identifier)
    )
    return db.scalars(stmt).unique().first()


def facet_counts(db: Session, column, q: OpportunityQuery) -> dict[str, int]:
    """Counts for one facet, with that facet's own filter removed."""
    stmt = apply_filters(select(column, func.count(Opportunity.id)).select_from(Opportunity), q)
    rows = db.execute(stmt.group_by(column)).all()
    return {str(value): int(count) for value, count in rows if value is not None}
