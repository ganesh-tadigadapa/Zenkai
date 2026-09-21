from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UTCDateTime, UUIDPrimaryKey, utcnow
from app.models.enums import (
    CostType,
    DataOrigin,
    UrlCheckStatus,
    VerificationMethod,
    VerificationStatus,
)


def content_fingerprint(title: str, organization_name: str, application_url: str | None) -> str:
    """Stable hash used to collapse the same opportunity arriving from several sources."""
    normalized = "|".join(
        part.strip().lower()
        for part in (title, organization_name, (application_url or "").split("?")[0])
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class Opportunity(UUIDPrimaryKey, Timestamps, Base):
    """A single discoverable opportunity.

    Design notes:
      * ``category`` is a closed enum (the six product categories) rather than a
        join table. Cross-cutting facets live in ``tags``/``secondary_categories``,
        which keeps every feed query a single indexed scan.
      * ``content_hash`` is unique and is what deduplication keys on.
      * ``verification_status`` and ``data_origin`` are independent: a seed record
        may be factually sourced but is never displayed as machine-verified.
    """

    __tablename__ = "opportunities"

    title: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(260), unique=True, index=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))

    category: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    secondary_categories: Mapped[list] = mapped_column(JSON, default=list)
    opportunity_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    summary: Mapped[str] = mapped_column(String(400), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility: Mapped[str | None] = mapped_column(Text)
    who_can_apply: Mapped[list] = mapped_column(JSON, default=list)

    location: Mapped[str] = mapped_column(String(160), default="Global")
    is_remote: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    cost_type: Mapped[str] = mapped_column(String(32), default=CostType.FREE.value, index=True)
    cost_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(8))

    deadline: Mapped[datetime | None] = mapped_column(UTCDateTime, index=True)
    is_rolling: Mapped[bool] = mapped_column(Boolean, default=False)
    # True when the date came from an extractor or a typical annual cycle rather
    # than a confirmed announcement. The UI renders these with a "~" and tells the
    # student to confirm on the official source.
    deadline_is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Where a student is sent. `source_url` is the authoritative provider page;
    # `direct_destination_url` is the exact page where they can actually start,
    # enrol, register or apply. It is NULL whenever that page could not be
    # established from an official source — the interface then falls back to the
    # provider page and says so, rather than guessing at a deep link.
    application_url: Mapped[str] = mapped_column(String(600), nullable=False)
    source_url: Mapped[str] = mapped_column(String(600), nullable=False)
    direct_destination_url: Mapped[str | None] = mapped_column(String(600))
    # Overrides the action derived from `opportunity_type`, for the rare record
    # whose destination does something other than its type implies.
    destination_action: Mapped[str | None] = mapped_column(String(32))
    last_url_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    url_check_status: Mapped[str] = mapped_column(
        String(16), default=UrlCheckStatus.UNCHECKED.value
    )

    skills: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    benefits: Mapped[list] = mapped_column(JSON, default=list)

    verification_status: Mapped[str] = mapped_column(
        String(24), default=VerificationStatus.NEEDS_REVIEW.value, index=True
    )
    # How the status above was reached. Kept separate from the status so the UI
    # can say "curated by hand" versus "the source was fetched" without guessing.
    verification_method: Mapped[str] = mapped_column(
        String(24), default=VerificationMethod.NONE.value
    )
    data_origin: Mapped[str] = mapped_column(String(16), default=DataOrigin.SEED.value, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1, from the extractor

    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    verified_by: Mapped[str | None] = mapped_column(String(160))
    last_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    discovered_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    # When the source itself published or last announced this opportunity, as
    # distinct from when we first recorded it. Null until a source reports it.
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    organization = relationship("Organization", back_populates="opportunities")
    source = relationship("Source")
    #: Category-specific facts. Present for certifications; the other five
    #: categories will gain their own detail tables the same way.
    credential = relationship(
        "CredentialDetail",
        back_populates="opportunity",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_opportunities_feed", "verification_status", "category", "deadline"),
    )
