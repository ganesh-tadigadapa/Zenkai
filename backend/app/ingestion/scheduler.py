"""Scheduling policy for source checks.

No scheduler daemon ships in this build. ``due_sources`` is the policy function a
cron job, APScheduler instance or Celery beat task would call; keeping it pure
makes the cadence testable without a running worker.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source


def is_due(source: Source, now: datetime | None = None) -> bool:
    if not source.active or not source.robots_allowed:
        return False
    if source.last_checked_at is None:
        return True
    now = now or datetime.now(timezone.utc)
    last = source.last_checked_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return now - last >= timedelta(minutes=source.check_frequency_minutes)


def due_sources(db: Session, now: datetime | None = None) -> list[Source]:
    sources = db.scalars(select(Source).where(Source.active.is_(True))).all()
    return [s for s in sources if is_due(s, now)]
