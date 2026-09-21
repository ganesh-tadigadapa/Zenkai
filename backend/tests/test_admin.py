"""Admin review queue, approval/rejection/edit, and route protection."""
from __future__ import annotations

from app.models.enums import Category, VerificationMethod, VerificationStatus
from app.services import review_service
from tests.conftest import ADMIN_HEADERS, make_opportunity


def test_admin_routes_refuse_anonymous_callers(client):
    for path in ("/api/v1/admin/stats", "/api/v1/admin/queue", "/api/v1/admin/sources"):
        assert client.get(path).status_code == 403


def test_admin_routes_reject_a_wrong_service_token(client):
    r = client.get("/api/v1/admin/stats", headers={"X-Admin-Token": "wrong"})
    assert r.status_code == 403


def test_admin_routes_refuse_a_signed_in_non_admin(client, student):
    """A normal account is identified, but must not reach the review queue."""
    assert client.get("/api/v1/admin/stats").status_code == 403


def test_admin_routes_accept_a_signed_in_reviewer(client, admin_user):
    """The is_admin flag authorises a person, with no shared token involved."""
    r = client.get("/api/v1/admin/stats")
    assert r.status_code == 200
    assert set(r.json()) == {"pending", "verified", "rejected", "expired"}


def test_queue_stats_count_each_status(db, client):
    make_opportunity(db, title="A", status=VerificationStatus.NEEDS_REVIEW)
    make_opportunity(db, title="B", status=VerificationStatus.NEEDS_REVIEW)
    make_opportunity(db, title="C", status=VerificationStatus.CURATED)
    make_opportunity(db, title="D", status=VerificationStatus.REJECTED)

    stats = client.get("/api/v1/admin/stats", headers=ADMIN_HEADERS).json()
    assert stats == {"pending": 2, "verified": 1, "rejected": 1, "expired": 0}


def test_queue_surfaces_lowest_confidence_first(db, client):
    make_opportunity(db, title="Confident", status=VerificationStatus.NEEDS_REVIEW, confidence=0.8)
    make_opportunity(db, title="Shaky", status=VerificationStatus.NEEDS_REVIEW, confidence=0.2)

    items = client.get("/api/v1/admin/queue", headers=ADMIN_HEADERS).json()["items"]
    assert [i["title"] for i in items] == ["Shaky", "Confident"]


def test_queue_can_be_filtered_by_status(db, client):
    make_opportunity(db, title="Pending", status=VerificationStatus.NEEDS_REVIEW)
    make_opportunity(db, title="Done", status=VerificationStatus.CURATED)

    verified = client.get("/api/v1/admin/queue?status=curated", headers=ADMIN_HEADERS).json()
    assert [i["title"] for i in verified["items"]] == ["Done"]


def test_approval_marks_source_checked_and_stamps_the_reviewer(db, client):
    row = make_opportunity(db, title="Needs Check", status=VerificationStatus.NEEDS_REVIEW)
    r = client.post(
        f"/api/v1/admin/opportunities/{row.id}/approve",
        headers=ADMIN_HEADERS,
        json={"reviewer": "alex", "notes": "Confirmed on the official page"},
    )
    assert r.status_code == 200
    assert r.json()["new_status"] == "source_checked"
    assert r.json()["previous_status"] == "needs_review"

    db.refresh(row)
    assert row.verification_status == VerificationStatus.SOURCE_CHECKED.value
    assert row.verification_method == VerificationMethod.HUMAN_REVIEW.value
    assert row.verified_by == "alex"
    assert row.verified_at is not None


def test_rejection_hides_the_record_from_the_public_feed(db, client):
    row = make_opportunity(db, title="Spam", status=VerificationStatus.NEEDS_REVIEW)
    client.post(
        f"/api/v1/admin/opportunities/{row.id}/reject",
        headers=ADMIN_HEADERS,
        json={"reviewer": "alex", "notes": "Not a real programme"},
    )
    db.refresh(row)
    assert row.verification_status == VerificationStatus.REJECTED.value
    assert client.get("/api/v1/opportunities").json()["total"] == 0


def test_edit_applies_changes_and_records_a_diff(db, client):
    row = make_opportunity(db, title="Typo Titel", status=VerificationStatus.NEEDS_REVIEW)
    r = client.post(
        f"/api/v1/admin/opportunities/{row.id}/edit",
        headers=ADMIN_HEADERS,
        json={
            "reviewer": "alex",
            "changes": {"title": "Corrected Title", "category": "scholarships"},
        },
    )
    assert r.status_code == 200
    db.refresh(row)
    assert row.title == "Corrected Title"
    assert row.category == Category.SCHOLARSHIPS.value

    history = client.get(
        f"/api/v1/admin/opportunities/{row.id}/history", headers=ADMIN_HEADERS
    ).json()
    assert history[0]["action"] == "edit"


def test_edit_ignores_fields_that_are_not_reviewable(db):
    row = make_opportunity(db, status=VerificationStatus.NEEDS_REVIEW)
    original_hash = row.content_hash
    review_service.edit(db, row, "alex", {"content_hash": "tampered", "title": "New Title"})
    assert row.content_hash == original_hash
    assert row.title == "New Title"


def test_review_history_is_append_only_and_newest_first(db, client):
    row = make_opportunity(db, status=VerificationStatus.NEEDS_REVIEW)
    client.post(f"/api/v1/admin/opportunities/{row.id}/edit", headers=ADMIN_HEADERS,
                json={"reviewer": "alex", "changes": {"title": "Edited"}})
    client.post(f"/api/v1/admin/opportunities/{row.id}/approve", headers=ADMIN_HEADERS,
                json={"reviewer": "sam"})

    history = client.get(
        f"/api/v1/admin/opportunities/{row.id}/history", headers=ADMIN_HEADERS
    ).json()
    assert len(history) == 2
    assert history[0]["action"] == "approve"
    assert history[0]["reviewer"] == "sam"


def test_acting_on_a_missing_opportunity_returns_404(client):
    r = client.post(
        "/api/v1/admin/opportunities/missing/approve",
        headers=ADMIN_HEADERS,
        json={"reviewer": "alex"},
    )
    assert r.status_code == 404


def test_admin_can_create_an_opportunity(client):
    payload = {
        "title": "Manually Added Programme",
        "organization_name": "Example Foundation",
        "category": "programs",
        "opportunity_type": "fellowship",
        "summary": "A programme added by a reviewer during triage.",
        "description": "A sufficiently long description for the record to be valid.",
        "application_url": "https://example.org/apply",
        "source_url": "https://example.org/",
    }
    r = client.post("/api/v1/admin/opportunities", headers=ADMIN_HEADERS, json=payload)
    assert r.status_code == 201
    assert r.json()["organization"]["name"] == "Example Foundation"
    assert r.json()["verification_status"] == "needs_review"


def test_creating_the_same_opportunity_twice_is_deduplicated(client):
    payload = {
        "title": "Duplicate Programme",
        "organization_name": "Example Foundation",
        "category": "programs",
        "opportunity_type": "fellowship",
        "summary": "A programme that will be submitted twice over.",
        "description": "A sufficiently long description for the record to be valid.",
        "application_url": "https://example.org/apply-twice",
        "source_url": "https://example.org/",
    }
    first = client.post("/api/v1/admin/opportunities", headers=ADMIN_HEADERS, json=payload)
    second = client.post("/api/v1/admin/opportunities", headers=ADMIN_HEADERS, json=payload)
    assert first.json()["id"] == second.json()["id"]


def test_invalid_payload_is_rejected(client):
    r = client.post(
        "/api/v1/admin/opportunities",
        headers=ADMIN_HEADERS,
        json={"title": "x", "organization_name": "Y", "category": "not_a_category"},
    )
    assert r.status_code == 422


def test_maintenance_expires_past_deadlines(db, client):
    row = make_opportunity(db, title="Gone", deadline_days=-2)
    r = client.post("/api/v1/admin/maintenance/expire", headers=ADMIN_HEADERS)
    assert r.json()["expired"] == 1
    db.refresh(row)
    assert row.verification_status == VerificationStatus.EXPIRED.value


def test_sources_can_be_listed_and_created(client):
    r = client.post(
        "/api/v1/admin/sources",
        headers=ADMIN_HEADERS,
        json={
            "name": "Example Feed",
            "url": "https://example.org/feed.xml",
            "source_type": "rss",
            "trust_level": 4,
        },
    )
    assert r.status_code == 201
    assert r.json()["active"] is True
    assert len(client.get("/api/v1/admin/sources", headers=ADMIN_HEADERS).json()) == 1
