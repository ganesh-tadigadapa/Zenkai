"""Sign-up, sign-in, sessions and isolation between accounts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    password_problems,
    verify_password,
)
from app.models.user import User, UserSession
from app.services import auth_service
from app.services.auth_service import AuthError
from tests.conftest import make_opportunity

SIGNUP = {"email": "New.Student@Example.com", "name": "New Student", "password": "a-good-password"}


# --- Hashing ----------------------------------------------------------------

def test_passwords_are_hashed_not_stored():
    hashed = hash_password("a-good-password")
    assert "a-good-password" not in hashed
    assert hashed.startswith("$argon2id$")


def test_the_same_password_hashes_differently_each_time():
    """Per-hash salting: two identical passwords must not share a digest."""
    assert hash_password("same-password") != hash_password("same-password")


def test_verification_accepts_the_right_password_and_rejects_others():
    hashed = hash_password("a-good-password")
    assert verify_password("a-good-password", hashed) is True
    assert verify_password("a-good-passwora", hashed) is False
    assert verify_password("", hashed) is False


def test_accounts_without_a_password_cannot_sign_in_with_one():
    """An identity-provider account has no password; that must not error."""
    assert verify_password("anything", None) is False


@pytest.mark.parametrize(
    "password,expected_ok",
    [("short", False), ("1234567890123", False), (" padded-password ", False),
     ("a-good-password", True)],
)
def test_password_rules(password, expected_ok):
    assert (password_problems(password) == []) is expected_ok


def test_session_tokens_are_stored_only_as_digests(db, student):
    token, session = auth_service.start_session(db, student)
    assert session.token_hash == hash_session_token(token)
    assert token not in session.token_hash
    # The plaintext token appears nowhere in the table.
    rows = db.query(UserSession).all()
    assert all(token != row.token_hash for row in rows)


def test_session_tokens_are_unique():
    assert len({generate_session_token() for _ in range(200)}) == 200


# --- Sign-up ----------------------------------------------------------------

def test_signup_creates_an_account_and_returns_a_session(client):
    r = client.post("/api/v1/auth/signup", json=SIGNUP)
    assert r.status_code == 201
    body = r.json()
    assert body["token"]
    assert body["user"]["name"] == "New Student"
    # Email is normalised, so casing cannot create a second account.
    assert body["user"]["email"] == "new.student@example.com"


def test_signup_response_never_contains_the_password(client):
    r = client.post("/api/v1/auth/signup", json=SIGNUP)
    assert SIGNUP["password"] not in r.text
    assert "password_hash" not in r.text


def test_signup_rejects_a_duplicate_email_regardless_of_casing(client):
    assert client.post("/api/v1/auth/signup", json=SIGNUP).status_code == 201
    again = client.post(
        "/api/v1/auth/signup", json={**SIGNUP, "email": "NEW.STUDENT@example.com"}
    )
    assert again.status_code == 400
    assert "already exists" in again.json()["detail"]


def test_signup_rejects_a_weak_password(client):
    r = client.post("/api/v1/auth/signup", json={**SIGNUP, "password": "short"})
    assert r.status_code == 400
    assert "10 characters" in r.json()["detail"]


def test_signup_rejects_an_invalid_email(client):
    r = client.post("/api/v1/auth/signup", json={**SIGNUP, "email": "not-an-email"})
    assert r.status_code == 422


# --- Sign-in ----------------------------------------------------------------

def test_login_succeeds_with_the_right_credentials(client):
    client.post("/api/v1/auth/signup", json=SIGNUP)
    r = client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]}
    )
    assert r.status_code == 200
    assert r.json()["token"]


def test_login_fails_identically_for_unknown_email_and_wrong_password(client):
    """The endpoint must not reveal which addresses have accounts."""
    client.post("/api/v1/auth/signup", json=SIGNUP)

    wrong_password = client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": "wrong-password-x"}
    )
    unknown_email = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong-password-x"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_login_updates_last_login(db, client):
    client.post("/api/v1/auth/signup", json=SIGNUP)
    user = auth_service.find_by_email(db, SIGNUP["email"])
    user.last_login_at = None
    db.flush()

    client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]}
    )
    db.refresh(user)
    assert user.last_login_at is not None


# --- Sessions ---------------------------------------------------------------

def test_a_session_grants_access_to_protected_routes(client):
    token = client.post("/api/v1/auth/signup", json=SIGNUP).json()["token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "new.student@example.com"


def test_logout_invalidates_the_session(client):
    token = client.post("/api/v1/auth/signup", json=SIGNUP).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_expired_sessions_do_not_resolve(db, student):
    token, session = auth_service.start_session(db, student)
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.flush()
    assert auth_service.resolve_session(db, token) is None


def test_a_resolved_expired_session_is_deleted(db, student):
    token, session = auth_service.start_session(db, student)
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.flush()
    auth_service.resolve_session(db, token)
    assert db.get(UserSession, session.id) is None


def test_malformed_authorization_headers_are_ignored(client, student):
    for header in ["", "Bearer", "Basic abc", "Bearer    ", "token abc"]:
        r = client.get("/api/v1/profile", headers={"Authorization": header})
        assert r.status_code == 401, header


def test_deleting_a_user_removes_their_sessions(db, student):
    """No orphaned sessions can outlive the account they belong to."""
    auth_service.start_session(db, student)
    assert db.query(UserSession).filter_by(user_id=student.id).count() > 0
    db.delete(student)
    db.flush()
    assert db.query(UserSession).filter_by(user_id=student.id).count() == 0


def test_purging_removes_only_expired_sessions(db, student):
    live, _ = auth_service.start_session(db, student)
    _, stale = auth_service.start_session(db, student)
    stale.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.flush()

    assert auth_service.purge_expired_sessions(db) == 1
    assert auth_service.resolve_session(db, live) is not None


# --- Isolation between accounts --------------------------------------------

def test_saved_opportunities_are_private_to_each_account(db, client, student):
    """The whole point of accounts: one student's list is not another's."""
    from app.core.security import hash_password as _hash

    row = make_opportunity(db, title="Shared Catalogue Item")
    client.post("/api/v1/saved", json={"opportunity_id": row.id})
    assert client.get("/api/v1/saved").json()["total"] == 1

    other = User(email="other@example.com", name="Other", password_hash=_hash("pw-123456789"))
    db.add(other)
    db.flush()
    other_token, _ = auth_service.start_session(db, other)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    assert client.get("/api/v1/saved", headers=other_headers).json()["total"] == 0
    # And the feed reflects each account's own state.
    mine = client.get("/api/v1/opportunities").json()["items"][0]
    theirs = client.get("/api/v1/opportunities", headers=other_headers).json()["items"][0]
    assert mine["is_saved"] is True
    assert theirs["is_saved"] is False


def test_preferences_are_private_to_each_account(db, client, student):
    from app.core.security import hash_password as _hash

    other = User(email="other2@example.com", name="Other", password_hash=_hash("pw-123456789"))
    db.add(other)
    db.flush()
    other_token, _ = auth_service.start_session(db, other)

    client.put("/api/v1/profile", json={"preferences": {"skills": ["Rust"], "interests": []}})

    mine = client.get("/api/v1/profile").json()
    theirs = client.get(
        "/api/v1/profile", headers={"Authorization": f"Bearer {other_token}"}
    ).json()
    assert mine["preferences"]["skills"] == ["Rust"]
    assert theirs["preferences"] is None


def test_saving_requires_an_account(db, client):
    row = make_opportunity(db)
    assert client.post("/api/v1/saved", json={"opportunity_id": row.id}).status_code == 401


def test_browsing_does_not_require_an_account(db, client):
    make_opportunity(db, title="Public Record")
    r = client.get("/api/v1/opportunities")
    assert r.status_code == 200
    assert r.json()["total"] == 1
    # Signed out, there is no per-user state to report.
    assert r.json()["items"][0]["is_saved"] is False
    assert r.json()["items"][0]["match"] is None


# --- Password change --------------------------------------------------------

def test_changing_password_requires_the_current_one(client):
    token = client.post("/api/v1/auth/signup", json=SIGNUP).json()["token"]
    r = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrong-password", "new_password": "another-good-password"},
    )
    assert r.status_code == 400


def test_changing_password_signs_out_other_devices(client, db):
    first = client.post("/api/v1/auth/signup", json=SIGNUP).json()["token"]
    second = client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]}
    ).json()["token"]

    r = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {second}"},
        json={"current_password": SIGNUP["password"], "new_password": "another-good-password"},
    )
    assert r.status_code == 200
    fresh = r.json()["token"]

    # Both old tokens are dead; the returned one works.
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {first}"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {second}"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh}"}).status_code == 200


def test_the_old_password_stops_working_after_a_change(client):
    token = client.post("/api/v1/auth/signup", json=SIGNUP).json()["token"]
    client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": SIGNUP["password"], "new_password": "another-good-password"},
    )
    old = client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]}
    )
    new = client.post(
        "/api/v1/auth/login", json={"email": SIGNUP["email"], "password": "another-good-password"}
    )
    assert old.status_code == 401
    assert new.status_code == 200


def test_registration_rejects_a_blank_name(db):
    with pytest.raises(AuthError):
        auth_service.register(db, "x@example.com", "   ", "a-good-password")


# --- Session validity, not merely presence ----------------------------------
#
# A cookie can outlive its session: it lasts 30 days, is revoked by signing out
# elsewhere or changing a password, and vanishes when the database is reseeded.
# The frontend once treated "a cookie exists" as "signed in", which bounced
# /login and the private routes off each other forever. These assert the API
# behaviour that fix depends on — an invalid token must be *distinguishable*
# from a valid one, not merely absent.

def test_a_token_that_no_longer_exists_is_rejected_not_ignored(client, student):
    """The API must answer 401, so the caller can tell stale from signed-out."""
    r = client.get("/api/v1/profile", headers={"Authorization": "Bearer vanished-token"})
    assert r.status_code == 401


def test_a_revoked_session_stops_resolving_immediately(db, client):
    token = client.post("/api/v1/auth/signup", json=SIGNUP).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/profile", headers=headers).status_code == 200

    client.post("/api/v1/auth/logout", headers=headers)
    assert client.get("/api/v1/profile", headers=headers).status_code == 401


def test_a_session_whose_user_was_deleted_does_not_resolve(db, student):
    """What a database reseed looks like: the row is gone, the token is not."""
    token, _ = auth_service.start_session(db, student)
    assert auth_service.resolve_session(db, token) is not None

    db.delete(student)
    db.flush()
    assert auth_service.resolve_session(db, token) is None


def test_resolving_a_stale_token_is_idempotent(db, student):
    """Repeated stale lookups must stay cheap and keep returning None."""
    token, session = auth_service.start_session(db, student)
    session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.flush()

    assert auth_service.resolve_session(db, token) is None
    assert auth_service.resolve_session(db, token) is None
