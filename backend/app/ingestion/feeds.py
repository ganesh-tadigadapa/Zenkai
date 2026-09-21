"""RSS 2.0 and Atom parsing.

Written against the standard library rather than pulling in a feed package.
The two formats are small and well specified, the registered sources are a
handful of well-formed vendor feeds, and a parser we own is one we can test
against fixtures instead of the live web.

Parsing is deliberately forgiving about *structure* and strict about
*content*: a missing element yields None, never a guess. Nothing here invents a
date, a link or a summary.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

ATOM_NS = "http://www.w3.org/2005/Atom"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"

#: ISO-8601 shapes Atom uses. RSS 2.0 uses RFC 822, handled separately.
_ISO_FORMATS = ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d")

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


@dataclass
class FeedEntry:
    """One item from a feed. Every optional field is genuinely optional."""

    title: str
    link: str | None = None
    summary: str = ""
    published_at: datetime | None = None
    entry_id: str | None = None
    categories: list[str] = field(default_factory=list)


@dataclass
class ParsedFeed:
    title: str | None
    entries: list[FeedEntry]
    #: "rss" or "atom" — recorded so a source's declared method can be checked
    #: against what it actually serves.
    format: str


class FeedParseError(ValueError):
    """The body was not a feed we can read. Raised, never silently swallowed."""


def strip_markup(value: str) -> str:
    """Feed summaries are usually escaped HTML. Reduce to readable text."""
    if not value:
        return ""
    text = html.unescape(value)
    text = _TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", html.unescape(text)).strip()


def parse_date(value: str | None) -> datetime | None:
    """Parse a feed date, or return None. Never guesses at 'now'."""
    if not value or not value.strip():
        return None
    raw = value.strip()

    # RSS 2.0: RFC 822, e.g. "Tue, 10 Feb 2026 09:00:00 +0000"
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass

    # Atom: ISO 8601. Python before 3.11 rejects a trailing "Z".
    for fmt in _ISO_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _text(element, path: str, namespaces: dict | None = None) -> str | None:
    found = element.find(path, namespaces) if namespaces else element.find(path)
    if found is None:
        return None
    value = (found.text or "").strip()
    return value or None


def _parse_rss(root) -> ParsedFeed:
    channel = root.find("channel")
    if channel is None:
        raise FeedParseError("RSS document has no <channel>")

    entries: list[FeedEntry] = []
    for item in channel.findall("item"):
        title = _text(item, "title")
        if not title:
            continue  # an item with no title tells us nothing usable
        encoded = item.find(f"{{{CONTENT_NS}}}encoded")
        body = (encoded.text if encoded is not None else None) or _text(item, "description") or ""
        entries.append(
            FeedEntry(
                title=strip_markup(title),
                link=_text(item, "link"),
                summary=strip_markup(body),
                published_at=parse_date(_text(item, "pubDate")),
                entry_id=_text(item, "guid"),
                categories=[
                    strip_markup(c.text) for c in item.findall("category") if (c.text or "").strip()
                ],
            )
        )
    return ParsedFeed(title=_text(channel, "title"), entries=entries, format="rss")


def _parse_atom(root) -> ParsedFeed:
    ns = {"a": ATOM_NS}
    entries: list[FeedEntry] = []

    for entry in root.findall("a:entry", ns):
        title = _text(entry, "a:title", ns)
        if not title:
            continue

        # Prefer the alternate link; fall back to whichever link has an href.
        link = None
        for candidate in entry.findall("a:link", ns):
            rel = candidate.get("rel", "alternate")
            href = candidate.get("href")
            if href and rel == "alternate":
                link = href
                break
            if href and link is None:
                link = href

        body = _text(entry, "a:content", ns) or _text(entry, "a:summary", ns) or ""
        entries.append(
            FeedEntry(
                title=strip_markup(title),
                link=link,
                summary=strip_markup(body),
                published_at=parse_date(
                    _text(entry, "a:published", ns) or _text(entry, "a:updated", ns)
                ),
                entry_id=_text(entry, "a:id", ns),
                categories=[
                    c.get("term", "").strip()
                    for c in entry.findall("a:category", ns)
                    if c.get("term")
                ],
            )
        )
    return ParsedFeed(title=_text(root, "a:title", ns), entries=entries, format="atom")


def parse_feed(body: str) -> ParsedFeed:
    """Parse an RSS 2.0 or Atom document.

    Raises FeedParseError for anything else, so a source quietly serving an
    error page is recorded as a failure rather than as an empty feed — which
    the mass-deletion guard would otherwise have to catch later.
    """
    if not body or not body.strip():
        raise FeedParseError("empty response body")
    try:
        root = ElementTree.fromstring(body.strip())
    except ElementTree.ParseError as exc:
        raise FeedParseError(f"not well-formed XML: {exc}") from exc

    tag = root.tag.split("}")[-1].lower()
    if tag == "rss":
        return _parse_rss(root)
    if tag == "feed":
        return _parse_atom(root)
    raise FeedParseError(f"unrecognised root element <{tag}>")
