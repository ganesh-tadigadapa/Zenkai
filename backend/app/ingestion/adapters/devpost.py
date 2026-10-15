"""Devpost hackathon listing API.

`devpost.com/api/hackathons` is the public JSON endpoint behind Devpost's own
hackathon listing, and robots.txt does not disallow it. Filtered to open and
upcoming events, it carries each hackathon's title, host, submission window,
themes, prize pool and whether it is online.

Deliberately *not* inferred:

* **cost** — entry is free on almost every Devpost hackathon, but the API does
  not say so, so it stays UNKNOWN rather than being assumed.
* **eligibility** — set per hackathon in its rules, which this endpoint does
  not carry.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.feeds import strip_markup
from app.models.source import Source

#: "Aug 31 - Oct 23, 2026", "Dec 01, 2026 - Jan 15, 2027", "Oct 01 - 23, 2026"
_FULL_DATE = re.compile(r"^([A-Z][a-z]{2})\s+(\d{1,2}),\s*(\d{4})$")
_DAY_YEAR = re.compile(r"^(\d{1,2}),\s*(\d{4})$")
_MONTH = re.compile(r"^([A-Z][a-z]{2})\b")
_TAG = re.compile(r"<[^>]+>")


def submission_deadline(period: str | None) -> datetime | None:
    """The last day of a Devpost submission window, end of day UTC.

    Returns None for anything it does not recognise rather than guessing.
    """
    if not period:
        return None
    if " - " in period:
        start, end = (part.strip() for part in period.rsplit(" - ", 1))
    else:
        start = end = period.strip()  # a one-day window: "Nov 01, 2026"

    match = _FULL_DATE.match(end)
    if match:
        month, day, year = match.groups()
    else:
        short = _DAY_YEAR.match(end)
        starts_with_month = _MONTH.match(start)
        if not (short and starts_with_month):
            return None
        day, year = short.groups()
        month = starts_with_month.group(1)
    try:
        date = datetime.strptime(f"{month} {day} {year}", "%b %d %Y")
    except ValueError:
        return None
    return date.replace(hour=23, minute=59, tzinfo=timezone.utc)


class DevpostAdapter(ApiAdapter):
    url_marker = "devpost.com/api/hackathons"
    name = "devpost"
    complete_listing = True

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        payload = json.loads(body)
        hackathons = payload.get("hackathons")
        if not isinstance(hackathons, list):
            raise ValueError("response carried no hackathons list")

        retrieved_at = datetime.now(timezone.utc)
        documents: list[RawDocument] = []
        for record in hackathons:
            title = (record.get("title") or "").strip()
            url = (record.get("url") or "").strip()
            if not title or not url or record.get("invite_only"):
                continue  # nothing to show, nowhere to send anyone, or closed to the public

            host = (record.get("organization_name") or "").strip() or "Devpost"
            location = ((record.get("displayed_location") or {}).get("location") or "").strip()
            online = location.lower() == "online"
            period = (record.get("submission_period_dates") or "").strip()
            deadline = submission_deadline(period)
            # "$<span data-currency-value>138,000</span>": drop the tags without
            # the space strip_markup would leave between "$" and the amount.
            prize = strip_markup(_TAG.sub("", record.get("prize_amount") or ""))
            themes = [t["name"] for t in record.get("themes") or [] if t.get("name")]

            lines = [f"{title} is a hackathon hosted by {host} on Devpost."]
            if period:
                lines.append(f"Submission period: {period}.")
            if prize and prize not in {"$0", "0"}:
                lines.append(f"Prizes: {prize} in total.")
            if themes:
                lines.append(f"Themes: {', '.join(themes)}.")
            lines.append("Online." if online else f"Location: {location or 'not stated'}.")

            documents.append(
                RawDocument(
                    url=url,
                    title=title,
                    # The first line already names the hackathon, so the title
                    # is not repeated ahead of it.
                    text=" ".join(lines),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": host,
                        "adapter": self.name,
                        "catalogue": "hackathons",
                        "opportunity_type": "hackathon",
                        "unpublished_fields": "cost",
                        "content_type": "application/json",
                        # Structured facts the pipeline applies over any guess
                        # read from the prose above. An empty deadline means
                        # the window could not be read, not that there is none.
                        "deadline": deadline.isoformat() if deadline else "",
                        "location": "Online" if online else (location or "Global"),
                        "is_remote": "true" if online else "false",
                        "tags": ",".join(themes),
                        "submission_period": period,
                        "devpost_id": str(record.get("id") or ""),
                    },
                )
            )
        return documents

    def next_page_url(self, body: str, current_url: str) -> str | None:
        payload = json.loads(body)
        meta = payload.get("meta") or {}
        total, per_page = meta.get("total_count"), meta.get("per_page")
        if not total or not per_page:
            return None

        parts = urlparse(current_url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        page = next((int(v) for k, v in query if k == "page" and v.isdigit()), 1)
        if page * per_page >= total:
            return None
        query = [(k, v) for k, v in query if k != "page"] + [("page", str(page + 1))]
        return urlunparse(parts._replace(query=urlencode(query, safe="[]")))
