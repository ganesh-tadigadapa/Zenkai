"""RSS and Atom connector.

Feeds are the preferred discovery path: they are published explicitly for
machine consumption, so reading one is what the provider asked for rather than
something tolerated.

The connector's only job is to turn a registered ``Source`` into
``RawDocument`` objects. It does not decide whether an entry is an opportunity
— that is the relevance gate's job, one stage later — so nothing here
interprets what it retrieved.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable

from app.ai.base import RawDocument
from app.ingestion.connectors.base import SourceConnector
from app.ingestion.feeds import FeedParseError, parse_feed
from app.ingestion.fetcher import FetchFailed, FetchRefused, PoliteFetcher
from app.models.enums import SourceType
from app.models.source import Source

logger = logging.getLogger(__name__)


class RSSConnector(SourceConnector):
    source_type = SourceType.RSS.value

    def __init__(self, fetcher: PoliteFetcher | None = None) -> None:
        #: Injectable so tests exercise the connector against fixtures rather
        #: than against the live web.
        self._fetcher = fetcher

    def can_handle(self, source: Source) -> bool:
        return source.source_type in (SourceType.RSS.value, SourceType.ATOM.value)

    def _fetch(self, source: Source) -> Iterable[RawDocument]:
        """Retrieve the feed and yield one document per entry.

        Raises rather than returning nothing when a fetch or parse fails: an
        empty result and a failure mean very different things to the pipeline's
        mass-deletion guard, and conflating them is how a broken connector
        retires a catalogue.
        """
        # A fetcher supplied by the caller is theirs to close; one we create is
        # ours. Tests inject one, which is also what keeps them off the network.
        if self._fetcher is not None:
            return self._read(self._fetcher, source)
        with PoliteFetcher() as fetcher:
            return self._read(fetcher, source)

    def _read(self, fetcher: PoliteFetcher, source: Source) -> list[RawDocument]:
        document = fetcher.get(source.url)
        try:
            feed = parse_feed(document.body)
        except FeedParseError as exc:
            raise FetchFailed(f"{source.url} did not serve a readable feed: {exc}") from exc

        if feed.format != source.discovery_method and source.discovery_method in {"rss", "atom"}:
            # Not an error — plenty of sources are registered as one and serve
            # the other — but worth knowing when the registry drifts.
            logger.info(
                "%s is registered as %s but served %s",
                source.name,
                source.discovery_method,
                feed.format,
            )

        documents: list[RawDocument] = []
        for entry in feed.entries:
            if not entry.link:
                # Without a link there is nowhere to send a student, and no
                # stable identity to deduplicate on.
                continue
            documents.append(
                RawDocument(
                    url=entry.link,
                    title=entry.title,
                    # Title and summary together, because the extractor reads
                    # the text and a feed summary alone often omits the subject.
                    text=f"{entry.title}\n\n{entry.summary}".strip(),
                    fetched_at=document.retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": source.organization or source.name,
                        "feed_url": source.url,
                        "feed_format": feed.format,
                        "feed_title": feed.title or "",
                        "content_type": document.content_type or "",
                        "published_at": entry.published_at.isoformat()
                        if entry.published_at
                        else "",
                        "entry_id": entry.entry_id or "",
                        "categories": ", ".join(entry.categories),
                    },
                )
            )

        logger.info("%s: %d entries from %s", source.name, len(documents), source.url)
        return documents
