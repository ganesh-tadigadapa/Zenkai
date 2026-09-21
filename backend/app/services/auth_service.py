"""Sign-up, sign-in and session lifecycle."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.providers import AuthError, ProviderIdentity
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    needs_rehash,
    password_problems,
    verify_password,
)
from app.models.user import User, UserSession

SESSION_TTL = timedelta(days=30)

# Same message whether the email is unknown or the password is wrong, so the
# endpoint cannot be used to enumerate which addresses have accounts.
GENERIC_LOGIN_FAILURE = "Email or password is incorrect."


def normalize_email(email: str) -> str:
    return email.strip().lower()


def find_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == normalize_email(email))).first()


def register(db: Session, email: str, name: str, password: str) -> User:
    """Create a password account. Raises AuthError with a readable reason."""
    email = normalize_email(email)
    name = name.strip()

    if not name:
        raise AuthError("Enter your name.")
    problems = password_problems(password)
    if problems:
        raise AuthError(" ".join(problems))
    if find_by_email(db, email) is not None:
        raise AuthError("An account with that email already exists.")

    user = User(
        email=email,
        name=name,
        password_hash=hash_password(password),
        auth_provider="password",
    )
    db.add(user)
    db.flush()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Verify a password login, transparently upgrading outdated hashes."""
    user = find_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError(GENERIC_LOGIN_FAILURE)

    # Re-hash in place when the parameters have moved on, so long-lived
    # accounts do not stay on weaker settings forever.
    if user.password_hash and needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    user.last_login_at = datetime.now(timezone.utc)
    return user


def upsert_from_provider(db: Session, identity: ProviderIdentity) -> User:
    """Entry point for a future OAuth provider. Links by verified email."""
    user = find_by_email(db, identity.email)
    if user is None:
        user = User(
            email=normalize_email(identity.email),
            name=identity.name.strip() or identity.email,
            auth_provider=identity.provider,
        )
        db.add(user)
        db.flush()
    user.last_login_at = datetime.now(timezone.utc)
    return user


def start_session(
    db: Session, user: User, user_agent: str | None = None
) -> tuple[str, UserSession]:
    """Create a session, returning the plaintext token and the stored row.

    The token is returned once and never persisted — only its digest is.
    """
    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + SESSION_TTL,
        user_agent=(user_agent or "")[:300] or None,
    )
    db.add(session)
    db.flush()
    return token, session


def resolve_session(db: Session, token: str) -> User | None:
    """Return the signed-in user, or None if the token is unknown or expired."""
    if not token:
        return None
    session = db.scalars(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    ).first()
    if session is None:
        return None

    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= datetime.now(timezone.utc):
        # Expired sessions are removed on sight rather than left to accumulate.
        db.delete(session)
        db.flush()
        return None

    return db.get(User, session.user_id)


def end_session(db: Session, token: str) -> bool:
    """Sign out. Returns True when a session was actually removed."""
    if not token:
        return False
    session = db.scalars(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    ).first()
    if session is None:
        return False
    db.delete(session)
    db.flush()
    return True


def end_all_sessions(db: Session, user: User) -> int:
    """Sign out everywhere — used after a password change."""
    result = db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.flush()
    return int(result.rowcount or 0)


def purge_expired_sessions(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    result = db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    db.flush()
    return int(result.rowcount or 0)


def change_password(db: Session, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        raise AuthError("Your current password is incorrect.")
    problems = password_problems(new)
    if problems:
        raise AuthError(" ".join(problems))
    user.password_hash = hash_password(new)
    db.flush()
