"""Housekeeping trims what has aged out and nothing a student can still see."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.enums import DataOrigin, VerificationStatus
from app.models.interaction import SavedOpportunity
from app.models.opportunity import Opportunity
from app.models.provenance import OpportunityProvenance, RawSourceDocument, SourceCheck
from app.models.source import Source
from app.models.user import UserSession
from app.services.housekeeping import tidy
from tests.conftest import make_opportunity

NOW = datetime.now(timezone.utc)
LONG_AGO = NOW - timedelta(days=400)


def _source(db) -> Source:
    source = Source(name="Test feed", url="https://example.com/feed", source_type="rss")
    db.add(source)
    db.flush()
    return source


def _raw(db, source, created_at, url="https://example.com/a") -> RawSourceDocument:
    raw = RawSourceDocument(source_id=source.id, url=url, content_hash=url, content="x",
                            created_at=created_at)
    db.add(raw)
    db.flush()
    return raw


def _closed(db, title, *, origin=DataOrigin.INGESTED, status=VerificationStatus.EXPIRED):
    opportunity = make_opportunity(db, title=title, status=status)
    opportunity.data_origin = origin.value
    db.flush()
    # Set after the flush, since updating the row stamps updated_at with now.
    db.execute(
        Opportunity.__table__.update()
        .where(Opportunity.id == opportunity.id)
        .values(updated_at=LONG_AGO)
    )
    return opportunity


def test_removes_old_checks_unlinked_documents_and_expired_sessions(db, student):
    source = _source(db)
    db.add(SourceCheck(source_id=source.id, started_at=LONG_AGO))
    db.add(SourceCheck(source_id=source.id, started_at=NOW))
    _raw(db, source, LONG_AGO, "https://example.com/old")
    _raw(db, source, NOW, "https://example.com/new")
    db.add(UserSession(user_id=student.id, token_hash="a" * 64, expires_at=NOW - timedelta(days=1)))
    db.flush()

    report = tidy(db, NOW)

    assert (report.checks, report.raw_documents, report.sessions) == (1, 1, 1)
    assert db.scalar(select(SourceCheck.started_at)) is not None
    assert [r.url for r in db.scalars(select(RawSourceDocument))] == ["https://example.com/new"]


def test_keeps_documents_that_a_record_still_points_to(db):
    source = _source(db)
    raw = _raw(db, source, LONG_AGO)
    opportunity = make_opportunity(db, title="Open Intern")
    db.add(OpportunityProvenance(opportunity_id=opportunity.id, source_id=source.id,
                                 raw_document_id=raw.id))
    db.flush()

    assert tidy(db, NOW).raw_documents == 0


def test_removes_long_closed_discovered_records_nobody_saved(db, student):
    gone = _closed(db, "Old Closed Intern")
    kept_saved = _closed(db, "Saved Closed Intern")
    kept_curated = _closed(db, "Curated Closed Thing", origin=DataOrigin.SEED)
    kept_open = make_opportunity(db, title="Still Open")
    db.add(SavedOpportunity(user_id=student.id, opportunity_id=kept_saved.id))
    db.flush()

    assert tidy(db, NOW).closed_records == 1

    remaining = set(db.scalars(select(Opportunity.title)))
    assert gone.title not in remaining
    assert {kept_saved.title, kept_curated.title, kept_open.title} <= remaining


def test_running_twice_is_harmless(db):
    _closed(db, "Old Closed Intern")
    tidy(db, NOW)
    assert str(tidy(db, NOW)).startswith("0 old source checks")
