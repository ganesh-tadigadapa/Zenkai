"""Per-provider adapters for official APIs.

Feeds share a format; APIs do not. Every catalogue has its own shape, so a
generic "API connector" can only do the fetching — turning one provider's JSON
into candidates needs provider-specific code.

An adapter is that code, and nothing else. It maps fields that are present and
leaves the rest alone: a value the API does not carry becomes None or UNKNOWN,
never a plausible-looking guess.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.base import RawDocument
from app.models.source import Source


class ApiAdapter(ABC):
    """Turns one provider's API response into RawDocuments."""

    #: Matched against a source's URL to choose an adapter.
    url_marker: str = ""
    name: str = "adapter"

    def handles(self, source: Source) -> bool:
        return bool(self.url_marker) and self.url_marker in source.url

    @abstractmethod
    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        """Parse a response body. Raises on anything it cannot read."""
        raise NotImplementedError
