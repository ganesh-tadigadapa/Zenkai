"""Change detection between what a source now says and what we already hold.

Two jobs:

1. Classify each sighting as NEW / UPDATED / UNCHANGED, and report which fields
   moved — a cost or a deadline changing is the kind of thing a reviewer must
   see, not something to overwrite silently.
2. Refuse to act on a result that looks like a broken connector rather than a
   genuinely emptied source. An outage returning zero items must not be allowed
   to retire a whole catalogue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.enums import ChangeKind
from app.models.opportunity import Opportunity

#: Fields whose movement matters enough to record and show a reviewer. A
#: description being reworded is not in the same class as a price appearing.
WATCHED_FIELDS: tuple[str, ...] = (
    "cost_type",
    "cost_amount",
    "deadline",
    "eligibility",
    "direct_destination_url",
    "source_url",
    "is_rolling",
    "location",
    "is_remote",
    "summary",
)

#: A run reporting fewer than this fraction of what we already hold is treated
#: as suspect rather than as a source that genuinely emptied out.
MIN_EXPECTED_RATIO = 0.5

#: Below this many existing records, ratios are meaningless, so the guard only
#: blocks a drop to literally nothing.
RATIO_FLOOR = 4


@dataclass
class FieldChange:
    field: str
    before: str | None
    after: str | None


@dataclass
class ChangeResult:
    kind: ChangeKind
    changes: list[FieldChange] = field(default_factory=list)

    @property
    def as_dict(self) -> dict:
        return {c.field: {"from": c.before, "to": c.after} for c in self.changes}


def _readable(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return moment.isoformat()
    return str(value)


def classify(existing: Opportunity | None, incoming: dict) -> ChangeResult:
    """Decide what a sighting means for a record we may already hold.

    ``incoming`` carries only the fields the source actually stated. A key that
    is absent was not mentioned, and absence never overwrites a value we have —
    a source going quiet about a price is not the same as it becoming free.
    """
    if existing is None:
        return ChangeResult(ChangeKind.NEW)

    changes: list[FieldChange] = []
    for name in WATCHED_FIELDS:
        if name not in incoming:
            continue  # not mentioned by this source
        new_value = incoming[name]
        if new_value is None:
            continue  # stated as unknown; keep what we have
        current = getattr(existing, name, None)
        if _readable(current) != _readable(new_value):
            changes.append(FieldChange(name, _readable(current), _readable(new_value)))

    return ChangeResult(ChangeKind.UPDATED if changes else ChangeKind.UNCHANGED, changes)


@dataclass
class SafetyVerdict:
    """Whether a run's results can be trusted enough to act on."""

    safe: bool
    reason: str


def is_result_plausible(
    retrieved: int, existing_count: int, connector_failed: bool = False
) -> SafetyVerdict:
    """Guard against a broken connector retiring records that still exist.

    Applies before anything is marked REMOVED or EXPIRED. Getting this wrong in
    the permissive direction empties the catalogue on a bad deploy; getting it
    wrong in the strict direction leaves a stale record for one more cycle. The
    second is obviously the cheaper mistake.
    """
    if connector_failed:
        return SafetyVerdict(False, "the connector failed, so its results say nothing")
    if existing_count == 0:
        return SafetyVerdict(True, "nothing held yet, so nothing can be lost")
    if retrieved == 0:
        return SafetyVerdict(
            False, "the source returned nothing while we hold records; treating as an outage"
        )
    if existing_count < RATIO_FLOOR:
        return SafetyVerdict(True, "too few records held for a ratio to mean anything")

    ratio = retrieved / existing_count
    if ratio < MIN_EXPECTED_RATIO:
        return SafetyVerdict(
            False,
            f"the source returned {retrieved} against {existing_count} held "
            f"({ratio:.0%}); treating as a partial failure",
        )
    return SafetyVerdict(True, f"returned {retrieved} against {existing_count} held")


def monitoring_summary(source) -> str:
    """One honest line about a source's monitoring state, for the UI."""
    if not source.has_been_checked:
        return "Not monitored yet."
    if source.last_success_at is None:
        return "Checked, but never read successfully."
    if source.consecutive_failures:
        return f"Last read successfully, then {source.consecutive_failures} failed attempt(s)."
    return "Monitored."
