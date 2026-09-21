from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import VerificationStatus
from app.models.interaction import SavedOpportunity
from app.models.opportunity import Opportunity
from app.models.user import User
from app.services import opportunity_service as svc


def save(db: Session, user: User, opportunity_id: str, notes: str | None = None) -> bool:
    """Idempotent save. Returns True when a new row was created."""
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise LookupError(opportunity_id)
    existing = db.get(SavedOpportunity, {"user_id": user.id, "opportunity_id": opportunity_id})
    if existing:
        if notes is not None:
            existing.notes = notes
        return False
    db.add(SavedOpportunity(user_id=user.id, opportunity_id=opportunity_id, notes=notes))
    db.flush()
    return True


def unsave(db: Session, user: User, opportunity_id: str) -> bool:
    existing = db.get(SavedOpportunity, {"user_id": user.id, "opportunity_id": opportunity_id})
    if existing is None:
        return False
    db.delete(existing)
    db.flush()
    return True


def list_saved(db: Session, user: User) -> dict:
    """Saved items split into what still matters and what has lapsed."""
    rows = db.scalars(
        select(SavedOpportunity)
        .where(SavedOpportunity.user_id == user.id)
        .options(
            joinedload(SavedOpportunity.opportunity).joinedload(Opportunity.organization),
            joinedload(SavedOpportunity.opportunity).joinedload(Opportunity.source),
        )
        .order_by(SavedOpportunity.created_at.desc())
    ).unique().all()

    now = datetime.now(timezone.utc)
    prefs = user.preferences
    saved_set = {r.opportunity_id for r in rows}
    active, expired = [], []
    for row in rows:
        opp = row.opportunity
        if opp is None:
            continue
        pair = (opp, svc.decorate(opp, prefs=prefs, saved=saved_set, now=now))
        left = pair[1]["days_left"]
        is_expired = (left is not None and left < 0) or (
            opp.verification_status == VerificationStatus.EXPIRED.value
        )
        (expired if is_expired else active).append(pair)

    active.sort(
        key=lambda p: (p[1]["days_left"] is None, p[1]["days_left"] if p[1]["days_left"] is not None else 0)
    )
    return {"active": active, "expired": expired}
