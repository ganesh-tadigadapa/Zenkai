"""Polite single-page fetcher.

Scope is intentionally narrow: fetch one known, permitted URL — the program page
a human already registered as a source. It is not a crawler and does not follow
links, enumerate paths, or bypass any access control. Robots.txt, Crawl-delay
and refusals are all handled by :class:`PoliteFetcher`.

Where a page adapter is registered for the URL (a calendar page that embeds its
listing as structured data, say), the adapter reads the page. Otherwise the page
becomes one document: its title, meta description and visible text.
"""
from __future__ import annotations

import html
import json
import logging
import re
from collections.abc import Iterable

from app.ai.base import RawDocument
from app.ingestion.adapters import adapter_for
from app.ingestion.connectors.base import SourceConnector
from app.ingestion.fetcher import FetchFailed, PoliteFetcher
from app.models.enums import SourceType
from app.models.source import Source

logger = logging.getLogger(__name__)

#: Enough text for the extractor; a whole page of navigation is not useful.
MAX_TEXT_CHARS = 4000

_DROP_BLOCKS = re.compile(
    r"<(script|style|noscript|svg|nav|header|footer|form|template)\b.*?</\1\s*>",
    re.S | re.I,
)
_COMMENTS = re.compile(r"<!--.*?-->", re.S)
_BLOCK_BREAKS = re.compile(r"</?(p|div|li|h[1-6]|br|section|article|tr)\b[^>]*>", re.I)
_TAGS = re.compile(r"<[^>]+>")
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
_META_DESCRIPTION = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:og:)?description["\'][^>]*content=["\']([^"\']*)',
    re.I,
)


def page_title(body: str) -> str:
    match = _TITLE.search(body)
    return " ".join(html.unescape(match.group(1)).split()) if match else ""


def page_text(body: str) -> str:
    """Visible text, one line per block, without scripts, styles or chrome."""
    text = _COMMENTS.sub(" ", body)
    text = _DROP_BLOCKS.sub(" ", text)
    text = _BLOCK_BREAKS.sub("\n", text)
    text = html.unescape(_TAGS.sub(" ", text))
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line)


class WebConnector(SourceConnector):
    source_type = SourceType.WEB.value

    def __init__(self, fetcher: PoliteFetcher | None = None) -> None:
        #: Injectable, which is what keeps the tests off the network.
        self._fetcher = fetcher

    def _fetch(self, source: Source) -> Iterable[RawDocument]:
        if self._fetcher is not None:
            return self._read(self._fetcher, source)
        with PoliteFetcher() as fetcher:
            return self._read(fetcher, source)

    def _read(self, fetcher, source: Source) -> list[RawDocument]:
        adapter = adapter_for(source)
        document = fetcher.get(source.url, max_bytes=adapter.max_bytes if adapter else None)

        if adapter is not None:
            try:
                documents = adapter.to_documents(document.body, source)
            except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
                raise FetchFailed(
                    f"{source.url} did not carry data the {adapter.name} adapter can read: {exc}"
                ) from exc
            logger.info("%s: %d records via %s", source.name, len(documents), adapter.name)
            return documents

        title = page_title(document.body)
        text = page_text(document.body)
        if not title or not text:
            # An empty result would look like a source that emptied out.
            raise FetchFailed(f"{source.url} returned a page with no readable content")

        description = _META_DESCRIPTION.search(document.body)
        lead = html.unescape(description.group(1)).strip() if description else ""
        body = "\n".join(part for part in (title, lead, text) if part)[:MAX_TEXT_CHARS]

        return [
            RawDocument(
                url=document.final_url,
                title=title,
                text=body,
                html=None,
                fetched_at=document.retrieved_at,
                source_id=source.id,
                metadata={
                    "organization": source.organization or source.name,
                    "content_type": document.content_type or "",
                    "page_url": source.url,
                    # The registry knows what kind of page this is.
                    **({"catalogue": source.category} if source.category else {}),
                },
            )
        ]
