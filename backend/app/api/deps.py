"""Request dependencies: identity and authorisation.

Identity comes from an opaque session token sent as ``Authorization: Bearer``.
The Next.js server holds that token in an httpOnly cookie and forwards it, so
it is never readable by browser JavaScript.

``ALLOW_DEMO_FALLBACK`` exists for local development only: with no token, the
request resolves to the seeded demo student so the app is usable straight after
seeding. It is off by default outside development, because a shared implicit
identity in production would let every visitor read and write the same account.
"""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services import auth_service


def db_session() -> Iterator[Session]:
    yield from get_db()


def bearer_token(
    authorization: str | None = Header(default=None),
) -> str | None:
    """Extract the session token from an Authorization header."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _demo_user(db: Session) -> User | None:
    if not settings.allow_demo_fallback:
        return None
    return db.scalars(select(User).where(User.email == settings.DEMO_USER_EMAIL)).first()


def get_optional_user(
    db: Session = Depends(db_session),
    token: str | None = Depends(bearer_token),
) -> User | None:
    """The signed-in user, or None. Used by surfaces that work signed out."""
    if token:
        user = auth_service.resolve_session(db, token)
        if user is not None:
            return user
        # A token that no longer resolves is simply not signed in — the caller
        # decides whether that is an error.
        return None
    return _demo_user(db)


def get_current_user(
    db: Session = Depends(db_session),
    token: str | None = Depends(bearer_token),
) -> User:
    """The signed-in user, required. 401 when there is no valid session."""
    user = get_optional_user(db=db, token=token)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(
    db: Session = Depends(db_session),
    token: str | None = Depends(bearer_token),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> User | None:
    """Admin gate.

    Two accepted paths, in order:

    1. A signed-in user whose ``is_admin`` flag is set. This is how the review
       queue authorises a person.
    2. The shared ``ADMIN_TOKEN``, kept as a service-account path for scripts
       and CI that have no session to present.

    The shared token is the weaker of the two and exists only so automation does
    not need to hold user credentials.
    """
    if token:
        user = auth_service.resolve_session(db, token)
        if user is not None and user.is_admin:
            return user

    if x_admin_token and x_admin_token == settings.ADMIN_TOKEN:
        return None  # service account: authorised, but not a person

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "You need reviewer access to do that.",
        headers={"WWW-Authenticate": "Bearer"},
    )
