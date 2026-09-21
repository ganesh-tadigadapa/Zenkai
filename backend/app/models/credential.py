from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps
from app.models.enums import (
    AssessmentType,
    CredentialType,
    DeliveryMode,
    ExperienceLevel,
    ProctoredStatus,
)


class CredentialDetail(Timestamps, Base):
    """Certification-specific facts, one row per opportunity.

    A separate table rather than more columns on ``Opportunity`` for two
    reasons. The shared row stays the same width for all six categories, which
    is what lets them share one discovery pipeline; and the other five
    categories can add their own detail tables without touching this one or
    each other.

    **Every field defaults to UNKNOWN or NULL.** A source that does not mention
    proctoring has not told us there is none, and a credential with no listed
    exam code does not have an empty one. Collapsing those to a definite answer
    is how a catalogue starts asserting things nobody verified.
    """

    __tablename__ = "credential_details"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )

    #: What the student ends up holding. A course completion certificate is not
    #: a professional certification, and this is where that distinction lives.
    credential_type: Mapped[str] = mapped_column(
        String(40), default=CredentialType.UNKNOWN.value, index=True
    )

    #: Subject areas, from the Specialization taxonomy. Drives search and
    #: matching, so it is a list rather than a single value.
    specializations: Mapped[list] = mapped_column(JSON, default=list)

    #: The issuing body, where it differs from the listing organisation — an
    #: exam sold through a training partner is still issued by the vendor.
    issuer: Mapped[str | None] = mapped_column(String(160))

    #: Vendor exam identifier, e.g. "AZ-900". A strong deduplication signal and
    #: what students actually search for.
    exam_code: Mapped[str | None] = mapped_column(String(40), index=True)

    #: Provider's own identifier for the item, for deduplication across sources.
    provider_id: Mapped[str | None] = mapped_column(String(120))

    assessment_type: Mapped[str] = mapped_column(
        String(32), default=AssessmentType.UNKNOWN.value, index=True
    )
    proctored_status: Mapped[str] = mapped_column(
        String(16), default=ProctoredStatus.UNKNOWN.value, index=True
    )
    delivery_mode: Mapped[str] = mapped_column(
        String(16), default=DeliveryMode.UNKNOWN.value, index=True
    )
    experience_level: Mapped[str] = mapped_column(
        String(16), default=ExperienceLevel.UNKNOWN.value, index=True
    )

    #: Study time the source states. NULL means unstated, not zero.
    duration_hours: Mapped[int | None] = mapped_column(Integer)
    #: How long the credential stays valid. NULL means unstated, not forever.
    validity_months: Mapped[int | None] = mapped_column(Integer)

    #: Countries where the source says it is available. Empty means unstated,
    #: which is not the same as worldwide.
    available_countries: Mapped[list] = mapped_column(JSON, default=list)

    opportunity = relationship("Opportunity", back_populates="credential")
