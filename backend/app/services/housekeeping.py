"""Keeps the database from growing without limit.

Discovery runs four times a day, forever, and every run leaves a trail: a
check row per source, raw documents for every listing that changed, and
records that close and are never shown again. None of that is a problem in a
month; on a 0.5 GB free database it is a problem in a year or two. This trims
what nobody reads any more, and runs at the end of every discovery run.

What it keeps, on purpose:

* raw documents still linked to a record's provenance - the audit trail;
* every open record, and any closed record somebody has saved;
* sessions that have not expired.

Postgres reuses the space freed by deleted rows (autovacuum), so trimming
regularly holds the database at a steady size instead of shrinking it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.models.enums import DataOrigin, VerificationStatus
from app.models.interaction import SavedOpportunity
from app.models.opportunity import Opportunity
from app.models.provenance import OpportunityProvenance, RawSourceDocument, SourceCheck
from app.models.user import UserSession

#: Source checks only feed the "last checked" view and recent failure counts.
CHECK_HISTORY = timedelta(days=60)
#: Raw documents no record points to any more (superseded versions, noise).
UNLINKED_RAW_DOCUMENTS = timedelta(days=30)
#: Closed, discovered records nobody saved. Long enough that a listing which
#: reopens next season is still recognised as the same one.
CLOSED_RECORDS = timedelta(days=365)


@dataclass
class TidyReport:
    checks: int = 0
    raw_documents: int = 0
    closed_records: int = 0
    sessions: int = 0

    def __str__(self) -> str:
        return (
            f"{self.checks} old source checks, {self.raw_documents} unlinked raw documents, "
            f"{self.closed_records} long-closed records, {self.sessions} expired sessions"
        )


def tidy(db: Session, now: datetime | None = None) -> TidyReport:
    """Delete what has aged out. Safe to run any number of times."""
    now = now or datetime.now(timezone.utc)
    report = TidyReport()

    # Closed records first, so the raw documents they pointed to become
    # unlinked and can go in the same pass once they are old enough.
    saved = exists().where(SavedOpportunity.opportunity_id == Opportunity.id)
    stale = select(Opportunity.id).where(
        Opportunity.data_origin == DataOrigin.INGESTED.value,
        Opportunity.verification_status.in_(
            [VerificationStatus.EXPIRED.value, VerificationStatus.REJECTED.value]
        ),
        Opportunity.updated_at < now - CLOSED_RECORDS,
        ~saved,
    )
    stale_ids = list(db.scalars(stale).all())
    for start in range(0, len(stale_ids), 500):
        batch = stale_ids[start : start + 500]
        # Deleted explicitly rather than trusting ON DELETE CASCADE, which
        # SQLite (used in tests and local runs) does not enforce by default.
        db.execute(delete(OpportunityProvenance).where(OpportunityProvenance.opportunity_id.in_(batch)))
        report.closed_records += db.execute(delete(Opportunity).where(Opportunity.id.in_(batch))).rowcount or 0

    linked = exists().where(OpportunityProvenance.raw_document_id == RawSourceDocument.id)
    report.raw_documents = db.execute(
        delete(RawSourceDocument)
        .where(RawSourceDocument.created_at < now - UNLINKED_RAW_DOCUMENTS, ~linked)
        .execution_options(synchronize_session=False)
    ).rowcount or 0

    report.checks = db.execute(
        delete(SourceCheck)
        .where(SourceCheck.started_at < now - CHECK_HISTORY)
        .execution_options(synchronize_session=False)
    ).rowcount or 0

    report.sessions = db.execute(
        delete(UserSession)
        .where(UserSession.expires_at < now)
        .execution_options(synchronize_session=False)
    ).rowcount or 0

    db.flush()
    return report
