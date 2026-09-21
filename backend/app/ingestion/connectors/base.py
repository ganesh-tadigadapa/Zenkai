"""Connector contract.

A connector's only job is to turn a :class:`Source` into ``RawDocument`` objects.
It must not interpret content — extraction is a separate, testable stage.

Compliance rules every connector inherits:
  * A source with ``robots_allowed=False`` is never fetched.
  * An inactive source is never fetched.
  * Connectors identify themselves with a descriptive User-Agent.
  * Connectors do not attempt to defeat CAPTCHAs, logins, or rate limits.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.ai.base import RawDocument
from app.models.source import Source

USER_AGENT = "ZenkaiBot/0.1 (+https://zenkai.dev/bot; opportunity discovery)"


class SourceConnector(ABC):
    """Base class for every ingestion connector."""

    source_type: str = "manual"

    def can_handle(self, source: Source) -> bool:
        return source.source_type == self.source_type

    def is_permitted(self, source: Source) -> tuple[bool, str]:
        """Compliance gate, checked before any network call."""
        if not source.active:
            return False, "source is inactive"
        if not source.robots_allowed:
            return False, "source disallows automated access"
        return True, "ok"

    def fetch(self, source: Source) -> Iterable[RawDocument]:
        permitted, reason = self.is_permitted(source)
        if not permitted:
            raise PermissionError(f"Refusing to fetch {source.url}: {reason}")
        return self._fetch(source)

    @abstractmethod
    def _fetch(self, source: Source) -> Iterable[RawDocument]:
        """Provider-specific retrieval. Implemented by subclasses."""
        raise NotImplementedError
