from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UTCDateTime, UUIDPrimaryKey
from app.models.enums import NotificationStatus


class SavedOpportunity(Timestamps, Base):
    __tablename__ = "saved_opportunities"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    opportunity = relationship("Opportunity")


class VerificationReview(UUIDPrimaryKey, Timestamps, Base):
    """Append-only audit trail for every human decision on an opportunity."""

    __tablename__ = "verification_reviews"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    reviewer: Mapped[str] = mapped_column(String(160), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(24))
    new_status: Mapped[str | None] = mapped_column(String(24))
    notes: Mapped[str | None] = mapped_column(Text)
    changes: Mapped[dict] = mapped_column(JSON, default=dict)


class Notification(UUIDPrimaryKey, Timestamps, Base):
    """Queued outbound message. The MVP only persists them; no channel sends yet."""

    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[str | None] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE")
    )
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=NotificationStatus.PENDING.value)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
