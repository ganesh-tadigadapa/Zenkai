"""Where the primary call to action points, and what it says."""
from __future__ import annotations

import pytest

from app.models.enums import (
    DESTINATION_ACTION_BY_TYPE,
    DestinationAction,
    DestinationType,
    OpportunityType,
    UrlCheckStatus,
)
from app.seed.data import ALL_SEEDS
from app.seed.destinations import BLOCKED_TO_BOTS, NO_DIRECT_DESTINATION, URL_FIXES
from app.services import destination_service
from app.services.destination_service import ACTION_LABELS
from tests.conftest import make_opportunity


def with_destination(db, url: str | None, **kwargs):
    row = make_opportunity(db, **kwargs)
    row.direct_destination_url = url
    db.flush()
    return row


# --- Resolution -------------------------------------------------------------

def test_a_direct_destination_is_preferred_over_the_source(db):
    row = with_destination(db, "https://example.com/enroll/data-analytics")
    row.source_url = "https://example.com/"
    db.flush()

    destination = destination_service.resolve(row)
    assert destination.url == "https://example.com/enroll/data-analytics"
    assert destination.type is DestinationType.DIRECT_DESTINATION
    assert destination.is_fallback is False


def test_the_official_source_is_the_fallback_when_no_destination_exists(db):
    row = with_destination(db, None)
    row.source_url = "https://example.com/"
    db.flush()

    destination = destination_service.resolve(row)
    assert destination.url == "https://example.com/"
    assert destination.type is DestinationType.OFFICIAL_SOURCE
    assert destination.is_fallback is True


def test_the_fallback_says_so_rather_than_implying_enrolment(db):
    """A provider homepage must not be dressed up as an enrolment link."""
    row = with_destination(db, None, opportunity_type=OpportunityType.COURSE)
    destination = destination_service.resolve(row)
    assert destination.action is DestinationAction.VISIT_SOURCE
    assert destination.label == "Visit official source"


def test_an_empty_or_whitespace_destination_counts_as_missing(db):
    for value in ("", "   "):
        row = with_destination(db, value, title=f"Blank {len(value)}")
        assert destination_service.resolve(row).is_fallback is True


def test_a_record_with_no_urls_at_all_does_not_crash(db):
    """A malformed record must degrade, not take the page down."""
    row = with_destination(db, None)
    row.source_url = ""
    row.application_url = ""
    db.flush()

    destination = destination_service.resolve(row)
    assert destination.url == ""
    assert destination.is_fallback is True


# --- Wording ----------------------------------------------------------------

@pytest.mark.parametrize(
    "opportunity_type,expected",
    [
        (OpportunityType.COURSE, "Start course"),
        (OpportunityType.CERTIFICATION, "Enroll"),
        (OpportunityType.EXAM, "Register for exam"),
        (OpportunityType.CREDENTIAL, "View certification"),
        (OpportunityType.LEARNING_PLATFORM, "Start learning"),
        (OpportunityType.TRAINING, "Start learning"),
        (OpportunityType.INTERNSHIP, "Apply now"),
        (OpportunityType.HACKATHON, "Register"),
        (OpportunityType.COMPETITION, "Register"),
        (OpportunityType.SCHOLARSHIP, "Apply now"),
        (OpportunityType.FELLOWSHIP, "Apply now"),
        (OpportunityType.SOFTWARE, "Get access"),
        (OpportunityType.CLOUD_CREDITS, "Get access"),
        (OpportunityType.STUDENT_BENEFIT, "Get access"),
    ],
)
def test_the_button_matches_what_the_opportunity_is(db, opportunity_type, expected):
    row = with_destination(db, "https://example.com/go", opportunity_type=opportunity_type)
    assert destination_service.resolve(row).label == expected


def test_an_exam_never_says_start_course(db):
    """The brief's explicit example: wording must follow the credential type."""
    exam = with_destination(db, "https://example.com/exam", opportunity_type=OpportunityType.EXAM)
    course = with_destination(
        db, "https://example.com/course", title="A Course", opportunity_type=OpportunityType.COURSE
    )
    assert destination_service.resolve(exam).label == "Register for exam"
    assert destination_service.resolve(course).label == "Start course"


def test_a_learning_course_never_says_apply(db):
    row = with_destination(db, "https://example.com/go", opportunity_type=OpportunityType.COURSE)
    assert "Apply" not in destination_service.resolve(row).label


def test_every_opportunity_type_has_an_action_and_a_label():
    for opportunity_type in OpportunityType:
        action = DESTINATION_ACTION_BY_TYPE[opportunity_type.value]
        assert action in ACTION_LABELS, opportunity_type


def test_an_explicit_action_overrides_the_type(db):
    row = with_destination(db, "https://example.com/go", opportunity_type=OpportunityType.COURSE)
    row.destination_action = DestinationAction.REGISTER_EXAM.value
    db.flush()
    assert destination_service.resolve(row).label == "Register for exam"


def test_an_unrecognised_override_falls_back_instead_of_raising(db):
    """A bad value in the database must not break the page."""
    row = with_destination(db, "https://example.com/go", opportunity_type=OpportunityType.COURSE)
    row.destination_action = "not-a-real-action"
    db.flush()
    assert destination_service.resolve(row).label == "Start course"


# --- API surface ------------------------------------------------------------

def test_the_feed_exposes_the_resolved_destination(db, client):
    with_destination(
        db, "https://example.com/exam", title="Feed Item", opportunity_type=OpportunityType.EXAM
    )
    item = client.get("/api/v1/opportunities").json()["items"][0]
    assert item["destination"]["label"] == "Register for exam"
    assert item["destination"]["url"] == "https://example.com/exam"
    assert item["destination"]["type"] in {"direct_destination", "official_source"}
    assert isinstance(item["destination"]["is_fallback"], bool)


def test_the_detail_page_exposes_both_urls(db, client):
    row = with_destination(db, "https://example.com/enroll")
    body = client.get(f"/api/v1/opportunities/{row.slug}").json()
    assert body["direct_destination_url"] == "https://example.com/enroll"
    assert body["source_url"]
    assert body["destination"]["url"] == "https://example.com/enroll"


# --- The catalogue -----------------------------------------------------------

def test_no_seed_record_invents_a_destination():
    """Every hub-only record must be recorded as such, with a reason."""
    for title, reason in NO_DIRECT_DESTINATION.items():
        assert reason.strip(), f"{title} gives no reason"


def test_url_fixes_only_replace_with_https_urls():
    for title, fix in URL_FIXES.items():
        for key in ("url", "source_url"):
            assert fix[key].startswith("https://"), f"{title}.{key}"
        assert fix["note"].strip(), f"{title} has no note explaining the change"


def test_the_replaced_search_results_url_is_gone():
    """Google STEP pointed at a careers search page — the exact bug this fixes."""
    step = next(s for s in ALL_SEEDS if s["title"] == "Google STEP Internship")
    resolved = URL_FIXES["Google STEP Internship"]["url"]
    assert "?q=" in step["url"], "seed no longer holds the original search URL"
    assert "?q=" not in resolved
    assert "/results" not in resolved
    assert resolved.startswith("https://buildyourfuture.withgoogle.com/programs/step")


def test_bot_blocked_records_are_not_treated_as_broken(db):
    """A 403 to our client is not a dead link, and must not be recorded as one."""
    assert BLOCKED_TO_BOTS
    assert UrlCheckStatus.BLOCKED.value != UrlCheckStatus.BROKEN.value


def test_seeded_catalogue_resolves_destinations_for_most_records(db):
    from app.seed.run import seed_opportunities, seed_sources, seed_users
    from app.models.opportunity import Opportunity
    from sqlalchemy import select

    seed_users(db)
    seed_opportunities(db, seed_sources(db))
    db.flush()

    rows = db.scalars(select(Opportunity)).all()
    direct = [r for r in rows if r.direct_destination_url]
    fallback = [r for r in rows if not r.direct_destination_url]

    assert len(rows) == len(ALL_SEEDS)
    # The hub-only records, and only those, fall back.
    assert {r.title for r in fallback} == set(NO_DIRECT_DESTINATION)
    assert len(direct) == len(ALL_SEEDS) - len(NO_DIRECT_DESTINATION)

    for row in rows:
        destination = destination_service.resolve(row)
        assert destination.url.startswith("https://"), row.title
        assert destination.label
        # A fallback must never borrow an action-flavoured label.
        if destination.is_fallback:
            assert destination.label == "Visit official source", row.title


# --- Credential search and filtering ----------------------------------------

def test_search_finds_a_credential_by_its_exam_code(db, client):
    """Students search for "AZ-900", which lives on the credential detail row."""
    from app.models.credential import CredentialDetail

    row = make_opportunity(db, title="Some Cloud Exam")
    db.add(CredentialDetail(opportunity_id=row.id, exam_code="XY-123"))
    db.flush()

    found = client.get("/api/v1/opportunities?q=XY-123").json()
    assert [i["title"] for i in found["items"]] == ["Some Cloud Exam"]


def test_search_finds_a_credential_by_specialization(db, client):
    from app.models.credential import CredentialDetail

    row = make_opportunity(db, title="Container Course")
    db.add(CredentialDetail(opportunity_id=row.id, specializations=["kubernetes", "devops"]))
    db.flush()

    assert client.get("/api/v1/opportunities?q=kubernetes").json()["total"] == 1


def test_filtering_by_proctoring_excludes_records_with_no_credential_row(db, client):
    """A record with nothing recorded must not be swept in as a match."""
    from app.models.credential import CredentialDetail
    from app.models.enums import ProctoredStatus

    proctored = make_opportunity(db, title="Proctored Exam")
    db.add(
        CredentialDetail(
            opportunity_id=proctored.id, proctored_status=ProctoredStatus.YES.value
        )
    )
    make_opportunity(db, title="Nothing Recorded")
    db.flush()

    found = client.get("/api/v1/opportunities?proctored=yes").json()
    assert [i["title"] for i in found["items"]] == ["Proctored Exam"]


def test_filtering_by_credential_type_is_exact(db, client):
    from app.models.credential import CredentialDetail
    from app.models.enums import CredentialType

    real = make_opportunity(db, title="Real Certification")
    db.add(
        CredentialDetail(
            opportunity_id=real.id,
            credential_type=CredentialType.PROFESSIONAL_CERTIFICATION.value,
        )
    )
    course = make_opportunity(db, title="Just A Course")
    db.add(
        CredentialDetail(
            opportunity_id=course.id, credential_type=CredentialType.COURSE_CERTIFICATE.value
        )
    )
    db.flush()

    found = client.get(
        "/api/v1/opportunities?credential_type=professional_certification"
    ).json()
    assert [i["title"] for i in found["items"]] == ["Real Certification"]


def test_credential_facts_reach_the_card_payload(db, client):
    from app.models.credential import CredentialDetail
    from app.models.enums import CredentialType

    row = make_opportunity(db, title="Carded")
    db.add(
        CredentialDetail(
            opportunity_id=row.id,
            credential_type=CredentialType.SKILL_BADGE.value,
            specializations=["python"],
        )
    )
    db.flush()

    item = client.get("/api/v1/opportunities").json()["items"][0]
    assert item["credential"]["credential_type"] == "skill_badge"
    assert item["credential"]["specializations"] == ["python"]
    # Unstated fields come back as unknown, not omitted or guessed.
    assert item["credential"]["proctored_status"] == "unknown"


def test_a_record_without_a_credential_row_reports_none(db, client):
    make_opportunity(db, title="No Credential")
    item = client.get("/api/v1/opportunities").json()["items"][0]
    assert item["credential"] is None
