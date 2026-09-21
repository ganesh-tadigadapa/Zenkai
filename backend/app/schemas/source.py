from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CheckFrequency, DiscoveryMethod, SourceAuthority, SourceType


class SourceCreate(BaseModel):
    name: str = Field(max_length=160)
    organization: str | None = Field(default=None, max_length=160)
    url: str = Field(max_length=500)
    official_url: str | None = Field(default=None, max_length=500)
    source_type: SourceType = SourceType.MANUAL
    category: str | None = None
    #: How much the source's word is worth. Defaults to UNKNOWN rather than
    #: assuming a new source is authoritative.
    authority: SourceAuthority = SourceAuthority.UNKNOWN
    #: What the source is known to offer. Never guessed.
    discovery_method: DiscoveryMethod = DiscoveryMethod.UNKNOWN
    trust_level: int = Field(default=3, ge=1, le=5)
    priority: int = Field(default=50, ge=0, le=100)
    check_frequency: CheckFrequency = CheckFrequency.NORMAL
    robots_allowed: bool = True
    access_notes: str | None = None


class SourceOut(SourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    active: bool
    check_frequency_minutes: int
    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    consecutive_failures: int = 0
    #: Whether this source can support a SOURCE_CHECKED record.
    is_authoritative: bool = False
    #: One honest line about monitoring state — "Not monitored yet." when
    #: nothing has ever read it, rather than an invented timestamp.
    monitoring_summary: str = "Not monitored yet."


class SourceCheckOut(BaseModel):
    """One recorded attempt to read a source, successful or not."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    started_at: datetime
    finished_at: datetime | None
    succeeded: bool
    failure_reason: str | None
    documents_retrieved: int
    candidates_extracted: int
    irrelevant_count: int
    created_count: int
    updated_count: int
    unchanged_count: int
    duplicate_count: int
