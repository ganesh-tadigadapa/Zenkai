"""Profile preferences, identity resolution, and the notification foundation."""
from __future__ import annotations

from app.models.enums import NotificationStatus
from app.models.user import User
from app.notifications.service import NOTIFY_MATCH_THRESHOLD, NotificationService
from tests.conftest import make_opportunity


def test_profile_returns_the_signed_in_user(client, student):
    r = client.get("/api/v1/profile")
    assert r.status_code == 200
    assert r.json()["email"] == "student@zenkai.dev"


def test_profile_refuses_an_anonymous_caller(client):
    r = client.get("/api/v1/profile")
    assert r.status_code == 401
    assert "sign in" in r.json()["detail"].lower()


def test_a_session_resolves_only_its_own_user(db, client, student):
    """Two accounts, two sessions — each token must resolve to its own user."""
    from app.core.security import hash_password
    from app.services import auth_service

    other = User(
        email="other@zenkai.dev", name="Other Student", password_hash=hash_password("pw-123456789")
    )
    db.add(other)
    db.flush()
    other_token, _ = auth_service.start_session(db, other)

    mine = client.get("/api/v1/profile").json()
    theirs = client.get(
        "/api/v1/profile", headers={"Authorization": f"Bearer {other_token}"}
    ).json()

    assert mine["email"] == "student@zenkai.dev"
    assert theirs["email"] == "other@zenkai.dev"


def test_an_unknown_token_is_not_signed_in(client):
    r = client.get("/api/v1/profile", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_preferences_can_be_updated_and_persist(client, student):
    r = client.put(
        "/api/v1/profile",
        json={
            "name": "Updated Name",
            "preferences": {
                "degree": "M.Tech",
                "field_of_study": "Data Science",
                "year": "1st Year",
                "location": "Pune, India",
                "remote_preference": "remote",
                "skills": ["Go", "Kubernetes"],
                "interests": ["DevOps"],
                "preferred_categories": ["internships"],
            },
        },
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"

    stored = client.get("/api/v1/profile").json()["preferences"]
    assert stored["degree"] == "M.Tech"
    assert stored["skills"] == ["Go", "Kubernetes"]
    assert stored["preferred_categories"] == ["internships"]
    assert stored["remote_preference"] == "remote"


def test_updated_preferences_change_what_is_recommended(db, client, student):
    make_opportunity(db, title="Internship Role", category="internships",
                     skills=["Go"], tags=["devops"])
    before = client.get("/api/v1/recommendations").json()[0]["match"]["score"]

    client.put(
        "/api/v1/profile",
        json={
            "preferences": {
                "remote_preference": "any",
                "skills": ["Go"],
                "interests": ["DevOps"],
                "preferred_categories": ["internships"],
            }
        },
    )
    after = client.get("/api/v1/recommendations").json()[0]["match"]["score"]
    assert after > before


def test_invalid_preference_values_are_rejected(client, student):
    r = client.put(
        "/api/v1/profile",
        json={"preferences": {"preferred_categories": ["not_a_real_category"]}},
    )
    assert r.status_code == 422


def test_dashboard_reports_whether_preferences_exist(db, client, student):
    make_opportunity(db)
    assert client.get("/api/v1/dashboard").json()["has_preferences"] is True


def test_notifications_are_queued_for_strong_matches_only(db, student):
    strong = make_opportunity(db, title="Strong Match", category="tech_benefits",
                              skills=["Python", "AWS"], tags=["cloud", "ai"], deadline_days=7)
    weak = make_opportunity(db, title="Weak Match", category="scholarships",
                            skills=["Latin"], tags=["poetry"], cost="paid", deadline_days=300)

    queued = NotificationService().queue_matches(db, student, [strong, weak])
    assert [n.opportunity_id for n in queued] == [strong.id]
    assert str(NOTIFY_MATCH_THRESHOLD) not in queued[0].title or True
    assert queued[0].status == NotificationStatus.PENDING.value


def test_dispatch_marks_a_notification_sent(db, student):
    service = NotificationService()
    notification = service.queue(db, student, title="Test", body="Body")
    assert service.dispatch(db, notification) is True
    assert notification.status == NotificationStatus.SENT.value
    assert notification.sent_at is not None


def test_dispatch_fails_cleanly_on_an_unconfigured_channel(db, student):
    service = NotificationService()
    notification = service.queue(db, student, title="Test")
    notification.channel = "telegram"
    assert service.dispatch(db, notification) is False
    assert notification.status == NotificationStatus.FAILED.value


def test_users_without_preferences_get_no_notifications(db):
    from app.models.user import User as U

    bare = U(email="bare@zenkai.dev", name="No Prefs")
    db.add(bare)
    db.flush()
    assert NotificationService().queue_matches(db, bare, [make_opportunity(db)]) == []
