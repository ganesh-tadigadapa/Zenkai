"""Official-API connector — the highest-trust discovery path.

The connector does the fetching; a per-provider adapter does the mapping,
because every catalogue API has its own shape. A source whose URL matches no
registered adapter fails loudly rather than being guessed at.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterable

from app.ai.base import RawDocument
from app.ingestion.adapters import adapter_for
from app.ingestion.connectors.base import SourceConnector
from app.ingestion.fetcher import FetchFailed, PoliteFetcher
from app.models.enums import SourceType
from app.models.source import Source

logger = logging.getLogger(__name__)


class APIConnector(SourceConnector):
    source_type = SourceType.OFFICIAL_API.value

    def __init__(self, fetcher: PoliteFetcher | None = None) -> None:
        #: Injectable, which is what keeps the tests off the network.
        self._fetcher = fetcher

    def _fetch(self, source: Source) -> Iterable[RawDocument]:
        adapter = adapter_for(source)
        if adapter is None:
            # Better to say so than to attempt a generic parse and produce
            # nonsense that then needs unpicking from the catalogue.
            raise FetchFailed(
                f"no API adapter is registered for {source.url} — "
                "add one under app/ingestion/adapters/"
            )

        if self._fetcher is not None:
            return self._read(self._fetcher, source, adapter)
        with PoliteFetcher() as fetcher:
            return self._read(fetcher, source, adapter)

    def _read(self, fetcher, source: Source, adapter) -> list[RawDocument]:
        document = fetcher.get(source.url)
        try:
            documents = adapter.to_documents(document.body, source)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            raise FetchFailed(
                f"{source.url} did not return a catalogue the {adapter.name} "
                f"adapter can read: {exc}"
            ) from exc

        logger.info("%s: %d records via %s", source.name, len(documents), adapter.name)
        return documents
