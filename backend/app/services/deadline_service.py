"""Deadline grouping for /deadlines."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.user import User
from app.repositories import opportunity_repository as repo
from app.repositories.opportunity_repository import OpportunityQuery
from app.services import opportunity_service as svc
from app.services.opportunity_service import PUBLIC_STATUSES

#: Rows sent per group. With live sources, hundreds of listings close within
#: the horizon; the page shows the nearest of each and links to the rest.
DEFAULT_PER_GROUP = 25


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


def grouped(
    db,
    user: User | None,
    horizon_days: int = 60,
    saved_only: bool = False,
    per_group: int = DEFAULT_PER_GROUP,
) -> tuple[dict, dict]:
    """Deadlines bucketed by urgency, soonest first within each bucket.

    Returns the first `per_group` rows of each bucket, decorated, and the full
    count of each bucket. Only the rows sent are decorated.
    """
    q = OpportunityQuery(
        sort="deadline",
        limit=2000,
        deadline_within_days=horizon_days,
        statuses=list(PUBLIC_STATUSES),
    )
    rows, _ = repo.search(db, q)
    saved = svc.saved_ids(db, user.id if user else None)
    if saved_only:
        rows = [row for row in rows if row.id in saved]

    now = now_utc()
    buckets: dict[str, list] = {"today": [], "this_week": [], "upcoming": []}
    for row in rows:
        days = svc.days_left(row, now)
        if days is None or days < 0:
            continue
        key = "today" if days == 0 else "this_week" if days <= 7 else "upcoming"
        buckets[key].append(row)

    prefs = user.preferences if user else None
    counts = {key: len(value) for key, value in buckets.items()}
    shown = {
        key: [(row, svc.decorate(row, prefs=prefs, saved=saved, now=now)) for row in value[:per_group]]
        for key, value in buckets.items()
    }
    return shown, counts


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
