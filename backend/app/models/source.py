from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UTCDateTime, UUIDPrimaryKey
from app.models.enums import (
    AUTHORITATIVE_SOURCES,
    CHECK_FREQUENCY_MINUTES,
    CheckFrequency,
    DiscoveryMethod,
    SourceAuthority,
    SourceType,
)


class Source(UUIDPrimaryKey, Timestamps, Base):
    """A registered origin of opportunity data.

    The registry is the one place that decides *whether* a source may be read
    and *how much its word is worth*. Two separate questions:

    * ``robots_allowed`` and ``enabled`` gate access. A source that disallows
      automated access is still registered — with the prohibition recorded as a
      fact — so the system holds an explicit note of what it must not touch.
    * ``authority`` gates belief. Only an authoritative source can support a
      record being published as SOURCE_CHECKED. A third-party listing is useful
      for discovering that something exists; it is not evidence of what it costs
      or who may apply.

    Nothing here is assumed. ``discovery_method`` defaults to UNKNOWN rather
    than guessing that a site offers an API, and the three timestamps stay NULL
    until something actually happens.
    """

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    #: The organisation behind the source, where it differs from the name.
    organization: Mapped[str | None] = mapped_column(String(160))

    #: Where we read from. Kept as `url` because existing code and data use it.
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    #: The organisation's authoritative page, when that is a different URL from
    #: the feed or endpoint we poll.
    official_url: Mapped[str | None] = mapped_column(String(500))

    source_type: Mapped[str] = mapped_column(String(32), default=SourceType.MANUAL.value)
    category: Mapped[str | None] = mapped_column(String(32))

    authority: Mapped[str] = mapped_column(
        String(32), default=SourceAuthority.UNKNOWN.value, index=True
    )
    discovery_method: Mapped[str] = mapped_column(
        String(24), default=DiscoveryMethod.UNKNOWN.value
    )

    #: Retained alongside `authority` as a within-tier tiebreaker and because
    #: the verification scorer already reads it.
    trust_level: Mapped[int] = mapped_column(Integer, default=3)  # 1 (low) .. 5 (official)

    #: `enabled` is the registry's own switch; `active` is kept as the legacy
    #: name that existing queries and the compliance gate already use.
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    #: Ordering hint when more sources are due than a run can process.
    priority: Mapped[int] = mapped_column(Integer, default=50)  # 0 (last) .. 100 (first)

    check_frequency: Mapped[str] = mapped_column(
        String(16), default=CheckFrequency.NORMAL.value
    )
    #: Derived from `check_frequency` on write, but overridable for a source
    #: that needs an unusual cadence.
    check_frequency_minutes: Mapped[int] = mapped_column(Integer, default=1440)

    last_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    last_success_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    last_failure_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    #: Consecutive failures. Used to back off a source that keeps breaking
    #: rather than hammering it on every cycle.
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    robots_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    access_notes: Mapped[str | None] = mapped_column(Text)

    # --- Derived helpers ---------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Registry switch. Aliases `active`, which predates this field."""
        return self.active

    @property
    def is_authoritative(self) -> bool:
        """Whether this source's word can support a SOURCE_CHECKED record."""
        return self.authority in AUTHORITATIVE_SOURCES

    @property
    def interval_minutes(self) -> int:
        """The cadence actually applied, honouring an explicit override."""
        default = CHECK_FREQUENCY_MINUTES.get(self.check_frequency, 1440)
        return self.check_frequency_minutes or default

    @property
    def has_been_checked(self) -> bool:
        return self.last_checked_at is not None
