"""Ingestion pipeline: extraction, deduplication, verification and compliance."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.ai import get_ai_client
from app.ai.base import ExtractedOpportunity, RawDocument
from app.ingestion.connectors import connector_for
from app.ingestion.connectors.base import SourceConnector
from app.ingestion.deduplication import DeduplicationService, title_similarity
from app.ingestion.extraction import OpportunityExtractor
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.scheduler import due_sources, is_due
from app.ingestion.verification import AUTO_APPROVE_CONFIDENCE, VerificationService
from app.models.enums import DataOrigin, SourceType, VerificationStatus
from app.models.source import Source
from tests.conftest import make_opportunity

FUTURE = (datetime.now(timezone.utc) + timedelta(days=45)).strftime("%Y-%m-%d")

SAMPLE = RawDocument(
    url="https://example.org/cloud-certification",
    title="Free Cloud Practitioner Certification",
    text=(
        "Free Cloud Practitioner Certification\n"
        "Eligibility: open to all enrolled university students worldwide.\n"
        f"Applications close on {FUTURE}.\n"
        "This certification is free for students and covers cloud fundamentals, "
        "security, billing and architecture. Participants complete a set of online "
        "modules and a final assessment, then receive a verifiable digital credential "
        "they can share with employers on their professional profiles."
    ),
    metadata={"organization": "Example Cloud"},
)


def test_stub_client_extracts_structured_fields():
    candidate = OpportunityExtractor().extract_one(SAMPLE)
    assert candidate is not None
    assert candidate.category == "certifications"
    assert candidate.deadline is not None
    assert "eligib" in (candidate.eligibility or "").lower()
    assert candidate.summary and len(candidate.summary) <= 245


def test_extractor_skips_empty_documents():
    assert OpportunityExtractor().extract_one(RawDocument(url="https://x.test")) is None


def test_stub_confidence_never_reaches_auto_approval():
    """Heuristic extraction must always end up in front of a human."""
    client = get_ai_client()
    candidate = client.extract(SAMPLE)
    assert candidate.confidence < AUTO_APPROVE_CONFIDENCE


def test_title_similarity_detects_near_duplicates():
    assert title_similarity("AWS Cloud Student Program", "AWS Cloud Student Program") == 1.0
    assert title_similarity("AWS Cloud Student Program", "Tuition Scholarship 2026") < 0.2


def test_deduplication_catches_an_identical_record(db):
    existing = make_opportunity(db, title="Cloud Thing")
    candidate = ExtractedOpportunity(
        title="Cloud Thing",
        organization_name=existing.organization.name,
        summary="s",
        description="d",
        application_url=existing.application_url,
    )
    verdict = DeduplicationService().check(db, candidate)
    assert verdict.is_duplicate is True
    assert verdict.existing_id == existing.id


def test_deduplication_allows_a_genuinely_new_record(db):
    make_opportunity(db, title="Cloud Thing")
    candidate = ExtractedOpportunity(
        title="Completely Different Scholarship Award",
        organization_name="Another Org",
        summary="s",
        description="d",
        application_url="https://example.org/other",
    )
    assert DeduplicationService().check(db, candidate).is_duplicate is False


def test_verification_routes_low_confidence_to_human_review():
    thin = ExtractedOpportunity(
        title="X", organization_name="Y", summary="s", description="short"
    )
    result = VerificationService().check(thin)
    assert result.status == VerificationStatus.NEEDS_REVIEW
    assert result.issues


def test_verification_flags_a_past_deadline_as_expired():
    stale = ExtractedOpportunity(
        title="Old Programme",
        organization_name="Y",
        summary="s",
        description="d" * 100,
        application_url="https://example.org/x",
        deadline=datetime.now(timezone.utc) - timedelta(days=3),
    )
    result = VerificationService().check(stale)
    assert result.status == VerificationStatus.EXPIRED
    assert result.checks["deadline_in_future"] is False


def test_verification_rewards_higher_source_trust():
    candidate = OpportunityExtractor().extract_one(SAMPLE)
    low = VerificationService().check(candidate, source_trust=1)
    high = VerificationService().check(candidate, source_trust=5)
    assert high.confidence > low.confidence


def test_pipeline_persists_a_candidate_for_review(db):
    report = IngestionPipeline().process_documents(db, [SAMPLE])
    assert report.extracted == 1
    assert report.created == 1

    from sqlalchemy import select

    from app.models.opportunity import Opportunity

    row = db.scalars(select(Opportunity)).first()
    assert row.data_origin == DataOrigin.INGESTED.value
    assert row.verification_status == VerificationStatus.NEEDS_REVIEW.value
    assert row.slug


def test_pipeline_is_idempotent_across_runs(db):
    """A second sighting of identical content creates nothing and changes nothing."""
    from sqlalchemy import func, select

    from app.models.opportunity import Opportunity

    pipeline = IngestionPipeline()
    pipeline.process_documents(db, [SAMPLE])
    second = pipeline.process_documents(db, [SAMPLE])

    assert second.created == 0
    assert second.unchanged == 1
    assert db.scalar(select(func.count()).select_from(Opportunity)) == 1


def test_connectors_refuse_sources_that_disallow_automated_access(db):
    blocked = Source(
        name="Blocked", url="https://example.org", source_type=SourceType.WEB.value,
        robots_allowed=False,
    )
    connector = connector_for(blocked)
    assert connector is not None
    permitted, reason = connector.is_permitted(blocked)
    assert permitted is False
    with pytest.raises(PermissionError):
        connector.fetch(blocked)


def test_connectors_refuse_inactive_sources():
    inactive = Source(
        name="Off", url="https://example.org", source_type=SourceType.RSS.value, active=False
    )
    with pytest.raises(PermissionError):
        connector_for(inactive).fetch(inactive)


def test_pipeline_reports_a_failed_fetch_without_raising(db):
    """A source that cannot be read is recorded as a failure, never a crash.

    Uses a fixture fetcher: no test in this suite touches the live web.
    """
    from app.ingestion.connectors.rss_connector import RSSConnector
    from app.ingestion.fetcher import FetchFailed
    from tests.conftest import FakeFetcher

    source = Source(
        name="Feed", url="https://example.org/feed", source_type=SourceType.RSS.value,
        active=True, robots_allowed=True, trust_level=4, check_frequency_minutes=720,
    )
    db.add(source)
    db.flush()

    connector = RSSConnector(
        fetcher=FakeFetcher({"https://example.org/feed": FetchFailed("HTTP 503")})
    )
    with pytest.raises(FetchFailed):
        list(connector.fetch(source))


def test_scheduler_only_returns_due_and_permitted_sources(db):
    now = datetime.now(timezone.utc)
    never = Source(name="Never checked", url="https://a.test", source_type="rss",
                   check_frequency_minutes=60, active=True, robots_allowed=True)
    recent = Source(name="Just checked", url="https://b.test", source_type="rss",
                    check_frequency_minutes=60, active=True, robots_allowed=True,
                    last_checked_at=now - timedelta(minutes=5))
    blocked = Source(name="Blocked", url="https://c.test", source_type="web",
                     check_frequency_minutes=60, active=True, robots_allowed=False)
    db.add_all([never, recent, blocked])
    db.flush()

    assert is_due(never) is True
    assert is_due(recent) is False
    assert is_due(blocked) is False
    assert [s.name for s in due_sources(db, now)] == ["Never checked"]


def test_base_connector_cannot_be_instantiated_without_fetch():
    with pytest.raises(TypeError):
        SourceConnector()
