from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UTCDateTime, UUIDPrimaryKey, utcnow
from app.models.enums import ChangeKind


def content_digest(text: str) -> str:
    """Stable digest of retrieved content, used to detect real change."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


class SourceCheck(UUIDPrimaryKey, Timestamps, Base):
    """One attempt to read a source.

    Recorded whether it succeeded or not, so "we have never managed to read
    this" is a visible fact rather than an absence. A source with no checks at
    all reports "Not monitored yet" instead of an invented timestamp.
    """

    __tablename__ = "source_checks"

    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    #: False when the connector raised, was refused, or returned nothing usable.
    succeeded: Mapped[bool] = mapped_column(default=False)
    #: Why it failed, in plain words, for whoever has to fix the connector.
    failure_reason: Mapped[str | None] = mapped_column(Text)

    documents_retrieved: Mapped[int] = mapped_column(Integer, default=0)
    candidates_extracted: Mapped[int] = mapped_column(Integer, default=0)
    #: Entries the relevance gate declined. On an announcement feed this is
    #: most of them, which is the gate doing its job rather than a failure.
    irrelevant_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)

    source = relationship("Source")


class RawSourceDocument(UUIDPrimaryKey, Timestamps, Base):
    """What a source actually returned, kept before anything interprets it.

    Extraction and normalisation will improve. Keeping the raw evidence means
    those improvements can be re-run over what we already have instead of
    re-fetching every source — which is both slower and ruder to the providers.

    It is also the audit trail: every published record can be traced back
    through source -> check -> this document -> extraction.

    **Never holds credentials.** Request headers, cookies and authorization
    values are not stored; `request_metadata` is limited to non-secret context
    such as the content type and the final URL after redirects.
    """

    __tablename__ = "raw_source_documents"

    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    check_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_checks.id", ondelete="SET NULL"), index=True
    )

    url: Mapped[str] = mapped_column(String(600), nullable=False)
    #: The URL actually served, after redirects, when it differs.
    final_url: Mapped[str | None] = mapped_column(String(600))
    title: Mapped[str | None] = mapped_column(String(300))

    #: The retrieved body. Text only — no binaries, no credentials.
    content: Mapped[str] = mapped_column(Text, default="")
    content_type: Mapped[str | None] = mapped_column(String(80))
    #: Digest of `content`. Equal digests across checks mean nothing changed,
    #: which is what makes UNCHANGED cheap to determine.
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    #: Non-secret context only: status code, content type, final URL.
    request_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    source = relationship("Source")

    __table_args__ = (Index("ix_raw_documents_url_hash", "url", "content_hash"),)


class OpportunityProvenance(UUIDPrimaryKey, Timestamps, Base):
    """Links a published opportunity to the evidence it came from.

    Many-to-one on purpose: several sources may describe the same opportunity,
    and merging them must not destroy the record of who said what. Deduplication
    adds a provenance row rather than discarding the second sighting.
    """

    __tablename__ = "opportunity_provenance"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    raw_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("raw_source_documents.id", ondelete="SET NULL")
    )

    #: What this sighting did to the record.
    change_kind: Mapped[str] = mapped_column(String(16), default=ChangeKind.NEW.value)
    #: Field-level diff when the sighting changed something, so a reviewer can
    #: see that a cost or deadline moved and what it moved from.
    changed_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    opportunity = relationship("Opportunity")
    source = relationship("Source")
    raw_document = relationship("RawSourceDocument")
