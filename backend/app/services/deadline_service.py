"""Deadline grouping for /deadlines."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.user import User
from app.repositories.opportunity_repository import OpportunityQuery
from app.services import opportunity_service as svc
from app.services.opportunity_service import PUBLIC_STATUSES


def urgency(days: int | None) -> str:
    if days is None:
        return "rolling"
    if days < 0:
        return "closed"
    if days == 0:
        return "today"
    if days <= 3:
        return "critical"
    if days <= 7:
        return "soon"
    return "upcoming"


def grouped(db, user: User | None, horizon_days: int = 60, saved_only: bool = False) -> dict:
    """Return deadlines bucketed by urgency, soonest first within each bucket."""
    q = OpportunityQuery(
        sort="deadline",
        limit=500,
        deadline_within_days=horizon_days,
        statuses=list(PUBLIC_STATUSES),
    )
    items, _ = svc.list_opportunities(db, q, user)
    if saved_only:
        items = [p for p in items if p[1]["is_saved"]]

    buckets: dict[str, list] = {"today": [], "this_week": [], "upcoming": []}
    for opp, meta in items:
        days = meta["days_left"]
        if days is None or days < 0:
            continue
        if days == 0:
            buckets["today"].append((opp, meta))
        elif days <= 7:
            buckets["this_week"].append((opp, meta))
        else:
            buckets["upcoming"].append((opp, meta))

    return buckets


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
