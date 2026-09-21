"""Polite single-page fetcher skeleton.

Scope is intentionally narrow: fetch one known, permitted URL — the program page
a human already registered as a source. It is not a crawler and does not follow
links, enumerate paths, or bypass any access control.
"""
from __future__ import annotations

from collections.abc import Iterable

from app.ai.base import RawDocument
from app.ingestion.connectors.base import SourceConnector
from app.models.enums import SourceType
from app.models.source import Source


class WebConnector(SourceConnector):
    source_type = SourceType.WEB.value

    def _fetch(self, source: Source) -> Iterable[RawDocument]:
        raise NotImplementedError(
            "Implement with httpx + a robots.txt check at request time, honouring "
            "Crawl-delay and the source's check_frequency_minutes."
        )
