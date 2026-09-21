from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UTCDateTime, UUIDPrimaryKey
from app.models.enums import RemotePreference


class User(UUIDPrimaryKey, Timestamps, Base):
    """An account.

    ``password_hash`` is nullable on purpose: an account created through an
    identity provider has no password, and the login path treats a null hash as
    "this account cannot sign in with a password" rather than as an error.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    password_hash: Mapped[str | None] = mapped_column(String(255))
    # Which provider owns this identity. "password" today; "github"/"google"
    # once the provider seam is implemented.
    auth_provider: Mapped[str] = mapped_column(String(32), default="password")
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    # Marks the seeded demo account so the UI can label it honestly.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def can_use_password(self) -> bool:
        return self.password_hash is not None


class UserSession(UUIDPrimaryKey, Timestamps, Base):
    """A signed-in session.

    Only the SHA-256 digest of the token is stored, so a database leak does not
    hand over live sessions. Rows are deleted on sign-out rather than flagged,
    which keeps "is this session valid?" a single indexed lookup.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    # Recorded for the "signed-in devices" view a future release will want, and
    # so a suspicious session can be recognised. Never shown to other users.
    user_agent: Mapped[str | None] = mapped_column(String(300))

    user = relationship("User", back_populates="sessions")

    __table_args__ = (Index("ix_user_sessions_lookup", "token_hash", "expires_at"),)


class UserPreferences(Timestamps, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    degree: Mapped[str | None] = mapped_column(String(80))
    field_of_study: Mapped[str | None] = mapped_column(String(120))
    year: Mapped[str | None] = mapped_column(String(40))
    country: Mapped[str | None] = mapped_column(String(80))
    location: Mapped[str | None] = mapped_column(String(160))
    remote_preference: Mapped[str] = mapped_column(String(16), default=RemotePreference.ANY.value)

    skills: Mapped[list] = mapped_column(JSON, default=list)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    preferred_categories: Mapped[list] = mapped_column(JSON, default=list)

    user = relationship("User", back_populates="preferences")
