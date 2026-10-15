"""MLH season events page.

`mlh.com/seasons/<year>/events` is MLH's official hackathon calendar. The page
embeds its event list as JSON for its own front end, so reading that is reading
the same structured data the page displays — one request, no crawling of the
individual event sites.

Only upcoming events are taken. Each carries its dates, format (in person,
online or hybrid), city and the event's own website, which is where a student
registers.

Deliberately *not* inferred: cost (MLH member events are free to attend, but
the page does not state it per event) and eligibility (set by each event).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.feeds import parse_date
from app.models.source import Source

_PAGE_DATA = re.compile(
    r'<script[^>]*data-page="app"[^>]*type="application/json"[^>]*>(.*?)</script>', re.S
)

FORMAT_LABEL = {"physical": "In person", "digital": "Online", "hybrid": "Hybrid"}


class MLHEventsAdapter(ApiAdapter):
    url_marker = "mlh.com/seasons/"
    name = "mlh"
    complete_listing = True

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        match = _PAGE_DATA.search(body)
        if not match:
            raise ValueError("page carried no embedded event data")
        props = (json.loads(match.group(1)) or {}).get("props") or {}
        events = props.get("upcomingEvents")
        if not isinstance(events, list):
            raise ValueError("page data carried no upcomingEvents list")

        retrieved_at = datetime.now(timezone.utc)
        documents: list[RawDocument] = []
        for event in events:
            name = (event.get("name") or "").strip()
            event_page = urljoin("https://www.mlh.com/", event.get("url") or "")
            website = (event.get("websiteUrl") or "").strip() or event_page
            if not name or not website:
                continue

            fmt = (event.get("formatType") or "").strip().lower()
            online = fmt == "digital"
            place = (event.get("location") or "").strip()
            starts = parse_date(event.get("startsAt"))
            ends = parse_date(event.get("endsAt"))
            focus = (event.get("customFields") or {}).get("hackathon_focus") or []

            lines = [f"{name} is an MLH member hackathon."]
            if starts:
                span = starts.strftime("%d %B %Y")
                if ends and ends.date() != starts.date():
                    span += f" to {ends.strftime('%d %B %Y')}"
                lines.append(f"Runs {span}.")
            lines.append(f"Format: {FORMAT_LABEL.get(fmt, 'not stated')}.")
            if place and not online:
                lines.append(f"Location: {place}.")
            if focus:
                lines.append(f"Focus: {', '.join(focus)}.")

            documents.append(
                RawDocument(
                    url=website,
                    title=name,
                    text=" ".join(lines),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": "Major League Hacking",
                        "adapter": self.name,
                        "catalogue": "hackathons",
                        "opportunity_type": "hackathon",
                        "unpublished_fields": "cost",
                        "content_type": "text/html",
                        # Registration closes when the event starts, so the
                        # start is the last day a student can act on it.
                        "deadline": starts.isoformat() if starts else "",
                        "location": "Online" if online else (place or "Global"),
                        "is_remote": "true" if online else "false",
                        "tags": ",".join(["MLH", *focus]),
                        "event_page": event_page,
                        "region": event.get("region") or "",
                        "mlh_id": event.get("id") or "",
                    },
                )
            )
        return documents
