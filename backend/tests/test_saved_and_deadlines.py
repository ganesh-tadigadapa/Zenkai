"""Saving opportunities and the deadline tracker."""
from __future__ import annotations

from app.models.enums import VerificationStatus
from app.services import deadline_service, saved_service
from tests.conftest import make_opportunity


def test_save_is_idempotent(db, client, student):
    row = make_opportunity(db)
    first = client.post("/api/v1/saved", json={"opportunity_id": row.id})
    second = client.post("/api/v1/saved", json={"opportunity_id": row.id})
    assert first.status_code == 201 and first.json()["created"] is True
    assert second.status_code == 201 and second.json()["created"] is False
    assert client.get("/api/v1/saved").json()["total"] == 1


def test_saving_an_unknown_opportunity_returns_404(client, student):
    assert client.post("/api/v1/saved", json={"opportunity_id": "nope"}).status_code == 404


def test_unsave_removes_the_record(db, client, student):
    row = make_opportunity(db)
    client.post("/api/v1/saved", json={"opportunity_id": row.id})
    assert client.delete(f"/api/v1/saved/{row.id}").json()["saved"] is False
    assert client.get("/api/v1/saved").json()["total"] == 0


def test_unsaving_something_not_saved_returns_404(db, client, student):
    row = make_opportunity(db)
    assert client.delete(f"/api/v1/saved/{row.id}").status_code == 404


def test_feed_reflects_saved_state(db, client, student):
    row = make_opportunity(db)
    assert client.get("/api/v1/opportunities").json()["items"][0]["is_saved"] is False
    client.post("/api/v1/saved", json={"opportunity_id": row.id})
    assert client.get("/api/v1/opportunities").json()["items"][0]["is_saved"] is True


def test_saved_list_separates_expired_entries(db, client, student):
    live = make_opportunity(db, title="Live One", deadline_days=5)
    dead = make_opportunity(db, title="Dead One", deadline_days=-3)
    saved_service.save(db, student, live.id)
    saved_service.save(db, student, dead.id)

    payload = client.get("/api/v1/saved").json()
    assert [i["title"] for i in payload["active"]] == ["Live One"]
    assert [i["title"] for i in payload["expired"]] == ["Dead One"]
    assert payload["total"] == 2


def test_saved_notes_are_stored(db, student):
    row = make_opportunity(db)
    saved_service.save(db, student, row.id, notes="Apply after exams")
    result = saved_service.list_saved(db, student)
    assert result["active"]


def test_deadline_buckets(db, client):
    make_opportunity(db, title="Today", deadline_days=0)
    make_opportunity(db, title="This Week", deadline_days=4)
    make_opportunity(db, title="Later", deadline_days=30)
    make_opportunity(db, title="Rolling", deadline_days=None, is_rolling=True)

    payload = client.get("/api/v1/deadlines").json()
    assert [i["title"] for i in payload["today"]] == ["Today"]
    assert [i["title"] for i in payload["this_week"]] == ["This Week"]
    assert [i["title"] for i in payload["upcoming"]] == ["Later"]
    assert payload["total"] == 3  # rolling entries carry no deadline


def test_deadline_buckets_are_sorted_by_urgency(db, client):
    make_opportunity(db, title="Day 6", deadline_days=6)
    make_opportunity(db, title="Day 2", deadline_days=2)
    payload = client.get("/api/v1/deadlines").json()
    assert [i["title"] for i in payload["this_week"]] == ["Day 2", "Day 6"]


def test_deadlines_can_be_limited_to_saved_items(db, client, student):
    keep = make_opportunity(db, title="Keep", deadline_days=3)
    make_opportunity(db, title="Ignore", deadline_days=3)
    saved_service.save(db, student, keep.id)

    payload = client.get("/api/v1/deadlines?saved_only=true").json()
    assert [i["title"] for i in payload["this_week"]] == ["Keep"]


def test_expired_records_never_appear_in_deadlines(db, client):
    make_opportunity(db, title="Expired", deadline_days=3, status=VerificationStatus.EXPIRED)
    assert client.get("/api/v1/deadlines").json()["total"] == 0


def test_urgency_labels():
    assert deadline_service.urgency(None) == "rolling"
    assert deadline_service.urgency(-1) == "closed"
    assert deadline_service.urgency(0) == "today"
    assert deadline_service.urgency(2) == "critical"
    assert deadline_service.urgency(6) == "soon"
    assert deadline_service.urgency(20) == "upcoming"


def test_dashboard_stats_reflect_the_database(db, client, student):
    make_opportunity(db, title="Soon", deadline_days=3)
    make_opportunity(db, title="Later", deadline_days=200)
    saved_service.save(db, student, make_opportunity(db, title="Saved One").id)

    stats = client.get("/api/v1/stats").json()
    assert stats["total"] == 3
    assert stats["closing_soon"] >= 1
    assert stats["saved"] == 1
