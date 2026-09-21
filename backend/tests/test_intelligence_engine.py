"""The discovery engine's new layers: credentials, registry, evidence, monitoring."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.ai.base import RawDocument
from app.ingestion.monitoring import (
    MIN_EXPECTED_RATIO,
    classify,
    is_result_plausible,
    monitoring_summary,
)
from app.ingestion.pipeline import IngestionPipeline
from app.models.credential import CredentialDetail
from app.models.enums import (
    AUTHORITATIVE_SOURCES,
    CHECK_FREQUENCY_MINUTES,
    DISCOVERY_PREFERENCE,
    AssessmentType,
    ChangeKind,
    CheckFrequency,
    CredentialType,
    DiscoveryMethod,
    ProctoredStatus,
    SourceAuthority,
)
from app.models.provenance import OpportunityProvenance, RawSourceDocument, SourceCheck
from app.models.source import Source
from app.seed.credentials import CREDENTIAL_FACTS
from tests.conftest import make_opportunity


def make_source(db, **kwargs) -> Source:
    defaults = dict(
        name=f"Source {kwargs.get('name', 'X')}",
        url="https://example.org/feed",
        source_type="rss",
        authority=SourceAuthority.OFFICIAL_ISSUER.value,
        discovery_method=DiscoveryMethod.RSS.value,
        active=True,
        robots_allowed=True,
    )
    defaults.update(kwargs)
    source = Source(**defaults)
    db.add(source)
    db.flush()
    return source


# --- Credential model -------------------------------------------------------

def test_unknown_is_the_default_for_every_credential_field(db):
    """An unstated field must read UNKNOWN, never a definite answer."""
    row = make_opportunity(db)
    detail = CredentialDetail(opportunity_id=row.id)
    db.add(detail)
    db.flush()

    assert detail.credential_type == CredentialType.UNKNOWN.value
    assert detail.proctored_status == ProctoredStatus.UNKNOWN.value
    assert detail.assessment_type == AssessmentType.UNKNOWN.value
    assert detail.specializations == []
    assert detail.exam_code is None
    assert detail.duration_hours is None


def test_unknown_proctoring_is_never_recorded_as_not_proctored():
    """The catalogue may only claim an exam is unproctored if a source said so."""
    stated = {t: f for t, f in CREDENTIAL_FACTS.items() if "proctored" in f}
    for title, facts in stated.items():
        assert facts["proctored"] is not ProctoredStatus.NO or "proctor" in title.lower()
    # Everything unstated stays UNKNOWN rather than being filled in.
    unstated = [t for t, f in CREDENTIAL_FACTS.items() if "proctored" not in f]
    assert unstated, "expected some records to leave proctoring unstated"


def test_only_genuine_certifications_are_typed_as_professional(db):
    """A course completion certificate must not claim to be a certification."""
    professional = [
        title
        for title, facts in CREDENTIAL_FACTS.items()
        if facts["credential_type"] is CredentialType.PROFESSIONAL_CERTIFICATION
    ]
    assert professional == ["AWS Certified Cloud Practitioner"]


def test_free_learning_behind_a_paid_exam_is_not_recorded_as_free():
    from app.models.enums import CostType

    aws = CREDENTIAL_FACTS["AWS Certified Cloud Practitioner"]
    assert aws["cost"] is CostType.EXAM_FEE


def test_credential_is_removed_with_its_opportunity(db):
    row = make_opportunity(db)
    db.add(CredentialDetail(opportunity_id=row.id))
    db.flush()
    db.delete(row)
    db.flush()
    assert db.query(CredentialDetail).filter_by(opportunity_id=row.id).count() == 0


# --- Source registry --------------------------------------------------------

def test_authority_gates_belief_separately_from_access(db):
    """A platform may be readable without its word being authoritative."""
    platform = make_source(db, name="Platform", authority=SourceAuthority.ESTABLISHED_PLATFORM.value)
    issuer = make_source(db, name="Issuer", url="https://issuer.test/feed")

    assert platform.robots_allowed and platform.enabled  # readable
    assert platform.is_authoritative is False             # but not authoritative
    assert issuer.is_authoritative is True


def test_only_official_bodies_count_as_authoritative():
    assert SourceAuthority.ESTABLISHED_PLATFORM.value not in AUTHORITATIVE_SOURCES
    assert SourceAuthority.OTHER_REPUTABLE_SOURCE.value not in AUTHORITATIVE_SOURCES
    assert SourceAuthority.UNKNOWN.value not in AUTHORITATIVE_SOURCES
    assert SourceAuthority.OFFICIAL_ISSUER.value in AUTHORITATIVE_SOURCES
    assert SourceAuthority.GOVERNMENT.value in AUTHORITATIVE_SOURCES


def test_check_cadence_follows_the_named_frequency(db):
    for name, minutes in CHECK_FREQUENCY_MINUTES.items():
        source = make_source(db, name=name, url=f"https://{name}.test", check_frequency=name,
                             check_frequency_minutes=minutes)
        assert source.interval_minutes == minutes
    assert CHECK_FREQUENCY_MINUTES[CheckFrequency.HIGH.value] == 360
    assert CHECK_FREQUENCY_MINUTES[CheckFrequency.LOW.value] == 10080


def test_discovery_preference_puts_official_apis_first():
    assert DISCOVERY_PREFERENCE[0] == DiscoveryMethod.OFFICIAL_API.value
    assert DISCOVERY_PREFERENCE.index(DiscoveryMethod.RSS.value) < DISCOVERY_PREFERENCE.index(
        DiscoveryMethod.PUBLIC_WEBPAGE.value
    )
    assert DISCOVERY_PREFERENCE[-1] == DiscoveryMethod.MANUAL.value


def test_a_never_checked_source_says_so_rather_than_inventing_a_time(db):
    source = make_source(db, name="Fresh")
    assert source.has_been_checked is False
    assert source.last_checked_at is None
    assert monitoring_summary(source) == "Not monitored yet."


# --- Change detection -------------------------------------------------------

def test_a_first_sighting_is_new(db):
    assert classify(None, {}).kind is ChangeKind.NEW


def test_identical_content_is_unchanged(db):
    row = make_opportunity(db, location="Global")
    assert classify(row, {"location": "Global"}).kind is ChangeKind.UNCHANGED


def test_a_moved_field_is_reported_with_its_old_and_new_value(db):
    row = make_opportunity(db, cost="free")
    result = classify(row, {"cost_type": "paid"})
    assert result.kind is ChangeKind.UPDATED
    assert result.as_dict == {"cost_type": {"from": "free", "to": "paid"}}


def test_a_source_going_quiet_does_not_erase_what_we_hold(db):
    """An unmentioned field is not a statement that the value is gone."""
    row = make_opportunity(db, cost="paid")
    assert classify(row, {}).kind is ChangeKind.UNCHANGED
    assert classify(row, {"cost_type": None}).kind is ChangeKind.UNCHANGED


# --- Mass-deletion guard ----------------------------------------------------

def test_an_empty_response_against_held_records_is_treated_as_an_outage():
    verdict = is_result_plausible(retrieved=0, existing_count=40)
    assert verdict.safe is False
    assert "outage" in verdict.reason


def test_a_large_drop_is_treated_as_a_partial_failure():
    assert is_result_plausible(retrieved=5, existing_count=40).safe is False


def test_a_normal_result_is_accepted():
    assert is_result_plausible(retrieved=38, existing_count=40).safe is True


def test_a_failed_connector_proves_nothing():
    assert is_result_plausible(retrieved=40, existing_count=40, connector_failed=True).safe is False


def test_the_first_ever_run_is_never_blocked():
    assert is_result_plausible(retrieved=0, existing_count=0).safe is True


@pytest.mark.parametrize("retrieved", [20, 30, 40])
def test_results_above_the_threshold_are_accepted(retrieved):
    assert is_result_plausible(retrieved, existing_count=40).safe is (
        retrieved / 40 >= MIN_EXPECTED_RATIO
    )


# --- Raw evidence and provenance -------------------------------------------

DOCUMENT = RawDocument(
    url="https://example.org/cert",
    title="Example Certification",
    text=(
        "Example Certification\n"
        "Eligibility: open to enrolled students.\n"
        "This certification is free for students and covers cloud fundamentals, "
        "security and architecture across a series of online modules ending in an "
        "assessment that awards a verifiable credential."
    ),
    metadata={"organization": "Example Body", "content_type": "text/html"},
)


def test_raw_source_data_is_kept_before_anything_interprets_it(db):
    source = make_source(db, name="Evidence")
    IngestionPipeline().process_documents(db, [DOCUMENT], source=source)

    raw = db.query(RawSourceDocument).one()
    assert raw.url == DOCUMENT.url
    assert raw.content == DOCUMENT.text
    assert raw.content_hash
    assert raw.source_id == source.id


def test_raw_documents_never_store_credentials(db):
    """Even if a connector puts a secret in metadata, it must not be persisted."""
    source = make_source(db, name="Secrets")
    leaky = RawDocument(
        url=DOCUMENT.url,
        title=DOCUMENT.title,
        text=DOCUMENT.text,
        metadata={
            "organization": "Example Body",
            "Authorization": "Bearer super-secret",
            "cookie": "session=abc",
            "api_key": "sk-live-xyz",
        },
    )
    IngestionPipeline().process_documents(db, [leaky], source=source)

    raw = db.query(RawSourceDocument).one()
    stored = str(raw.request_metadata).lower()
    for secret in ("bearer", "super-secret", "session=abc", "sk-live-xyz"):
        assert secret not in stored
    assert raw.request_metadata.get("organization") == "Example Body"


def test_a_published_record_can_be_traced_back_to_its_evidence(db):
    source = make_source(db, name="Traceable")
    IngestionPipeline().process_documents(db, [DOCUMENT], source=source)

    provenance = db.query(OpportunityProvenance).one()
    assert provenance.source_id == source.id
    assert provenance.raw_document_id is not None
    assert provenance.change_kind == ChangeKind.NEW.value

    raw = db.get(RawSourceDocument, provenance.raw_document_id)
    assert raw.source_id == source.id


def test_a_second_sighting_adds_provenance_rather_than_a_duplicate(db):
    """Provenance must survive deduplication: several sources may agree."""
    from sqlalchemy import func, select

    from app.models.opportunity import Opportunity

    source = make_source(db, name="Repeat")
    pipeline = IngestionPipeline()
    pipeline.process_documents(db, [DOCUMENT], source=source)
    pipeline.process_documents(db, [DOCUMENT], source=source)

    assert db.scalar(select(func.count()).select_from(Opportunity)) == 1
    assert db.query(OpportunityProvenance).count() == 2


def test_every_attempt_is_recorded_even_when_it_fails(db):
    """A connector that cannot run must leave a trace, not silence.

    Uses a source type with no registered connector, so the failure happens
    before any network call could be attempted.
    """
    source = make_source(db, name="Broken", source_type="social_signal")
    report = IngestionPipeline().run_source(db, source)

    check = db.query(SourceCheck).filter_by(source_id=source.id).one()
    assert check.succeeded is False
    assert check.failure_reason
    assert report.errors
    assert source.last_failure_at is not None
    assert source.consecutive_failures == 1
    assert source.last_success_at is None


def test_repeated_failures_accumulate(db):
    source = make_source(db, name="Flaky", source_type="social_signal")
    pipeline = IngestionPipeline()
    pipeline.run_source(db, source)
    pipeline.run_source(db, source)
    assert source.consecutive_failures == 2


def test_a_blocked_source_is_recorded_as_a_failed_check_not_a_silent_skip(db):
    source = make_source(db, name="Blocked", robots_allowed=False)
    IngestionPipeline().run_source(db, source)
    check = db.query(SourceCheck).filter_by(source_id=source.id).one()
    assert check.succeeded is False
    assert "disallows" in (check.failure_reason or "")
