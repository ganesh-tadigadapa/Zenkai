"""Human verification workflow.

Automation proposes; a reviewer decides. Every decision writes an immutable
``VerificationReview`` row so we can audit how a record reached its status.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import ReviewAction, VerificationMethod, VerificationStatus
from app.models.interaction import VerificationReview
from app.models.opportunity import Opportunity


def queue(db: Session, status: str, limit: int = 50, offset: int = 0):
    stmt = (
        select(Opportunity)
        .where(Opportunity.verification_status == status)
        .options(joinedload(Opportunity.organization), joinedload(Opportunity.source))
        .order_by(Opportunity.confidence.asc(), Opportunity.discovered_at.desc())
        .limit(limit)
        .offset(offset)
    )
    total = db.scalar(
        select(func.count()).select_from(Opportunity).where(
            Opportunity.verification_status == status
        )
    )
    return list(db.scalars(stmt).unique().all()), int(total or 0)


def queue_stats(db: Session) -> dict:
    rows = db.execute(
        select(Opportunity.verification_status, func.count(Opportunity.id)).group_by(
            Opportunity.verification_status
        )
    ).all()
    counts = {status: int(count) for status, count in rows}
    return {
        "pending": counts.get(VerificationStatus.NEEDS_REVIEW.value, 0),
        "verified": counts.get(VerificationStatus.CURATED.value, 0)
        + counts.get(VerificationStatus.SOURCE_CHECKED.value, 0),
        "rejected": counts.get(VerificationStatus.REJECTED.value, 0),
        "expired": counts.get(VerificationStatus.EXPIRED.value, 0),
    }


def _record(
    db: Session,
    opportunity: Opportunity,
    action: ReviewAction,
    reviewer: str,
    previous: str,
    notes: str | None,
    changes: dict | None = None,
) -> VerificationReview:
    review = VerificationReview(
        opportunity_id=opportunity.id,
        reviewer=reviewer,
        action=action.value,
        previous_status=previous,
        new_status=opportunity.verification_status,
        notes=notes,
        changes=changes or {},
    )
    db.add(review)
    db.flush()
    return review


def approve(db: Session, opportunity: Opportunity, reviewer: str, notes: str | None = None):
    previous = opportunity.verification_status
    now = datetime.now(timezone.utc)
    # A reviewer approving in the queue means they opened the official source.
    opportunity.verification_status = VerificationStatus.SOURCE_CHECKED.value
    opportunity.verification_method = VerificationMethod.HUMAN_REVIEW.value
    opportunity.verified_at = now
    opportunity.verified_by = reviewer
    opportunity.last_checked_at = now
    return _record(db, opportunity, ReviewAction.APPROVE, reviewer, previous, notes)


def reject(db: Session, opportunity: Opportunity, reviewer: str, notes: str | None = None):
    previous = opportunity.verification_status
    opportunity.verification_status = VerificationStatus.REJECTED.value
    opportunity.verification_method = VerificationMethod.HUMAN_REVIEW.value
    opportunity.verified_by = reviewer
    opportunity.last_checked_at = datetime.now(timezone.utc)
    return _record(db, opportunity, ReviewAction.REJECT, reviewer, previous, notes)


EDITABLE = {
    "title", "summary", "description", "eligibility", "deadline", "location",
    "is_remote", "cost_type", "category", "opportunity_type", "skills", "tags", "benefits",
}


def edit(db: Session, opportunity: Opportunity, reviewer: str, changes: dict, notes: str | None = None):
    applied: dict = {}
    for key, value in changes.items():
        if key not in EDITABLE or value is None:
            continue
        current = getattr(opportunity, key)
        new_value = value.value if hasattr(value, "value") else value
        if current != new_value:
            applied[key] = {"from": str(current), "to": str(new_value)}
            setattr(opportunity, key, new_value)
    opportunity.last_checked_at = datetime.now(timezone.utc)
    return _record(
        db, opportunity, ReviewAction.EDIT, reviewer, opportunity.verification_status, notes, applied
    )


def history(db: Session, opportunity_id: str):
    return list(
        db.scalars(
            select(VerificationReview)
            .where(VerificationReview.opportunity_id == opportunity_id)
            .order_by(VerificationReview.created_at.desc())
        ).all()
    )
