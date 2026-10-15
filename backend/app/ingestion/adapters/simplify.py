"""SimplifyJobs internship listings.

The `SimplifyJobs/Summer<year>-Internships` repository on GitHub is a widely
used, openly maintained list of tech internships. Its `listings.json` is the
data behind the README table: every posting with company, title, locations,
the employer's own application link, and an `active` flag maintainers clear
when a role closes.

The file holds every posting ever listed (17,000+), so only visible, active
ones are read, newest first, up to :data:`MAX_LISTINGS`. The listing is
treated as complete for that window: a role whose flag is cleared, or that
ages out of the window, is retired on the next run.

Postings carry no deadline — internships close when they fill — so none is
set, and cost and eligibility are not stated.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.models.source import Source

MAX_LISTINGS = 300


class SimplifyInternshipsAdapter(ApiAdapter):
    url_marker = "SimplifyJobs/"
    name = "simplify"
    complete_listing = True
    #: listings.json is ~13 MB.
    max_bytes = 40 * 1024 * 1024

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        listings = json.loads(body)
        if not isinstance(listings, list):
            raise ValueError("listings.json is not a list")

        current = [
            item
            for item in listings
            if item.get("active") and item.get("is_visible", True) and item.get("url")
        ]
        current.sort(key=lambda item: item.get("date_posted") or 0, reverse=True)

        retrieved_at = datetime.now(timezone.utc)
        documents: list[RawDocument] = []
        for item in current[:MAX_LISTINGS]:
            title = (item.get("title") or "").strip()
            company = (item.get("company_name") or "").strip()
            if not title or not company:
                continue
            locations = [loc for loc in item.get("locations") or [] if loc]
            remote = any("remote" in loc.lower() for loc in locations)
            terms = [t for t in item.get("terms") or [] if t and t != "N/A"]
            category = (item.get("category") or "").strip()
            posted = item.get("date_posted")
            posted_on = (
                datetime.fromtimestamp(posted, tz=timezone.utc).strftime("%d %B %Y") if posted else ""
            )

            lines = [f"{title} at {company}."]
            if terms:
                lines.append(f"Term: {', '.join(terms)}.")
            if locations:
                lines.append(f"Location: {'; '.join(locations[:4])}.")
            if category:
                lines.append(f"Area: {category}.")
            if posted_on:
                lines.append(f"Posted {posted_on}.")

            documents.append(
                RawDocument(
                    url=item["url"].strip(),
                    title=f"{title} — {company}",
                    text=" ".join(lines),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": company,
                        "adapter": self.name,
                        "catalogue": "internships",
                        "opportunity_type": "internship",
                        "unpublished_fields": "cost",
                        "content_type": "application/json",
                        # Internships close when filled; there is no date.
                        "deadline": "",
                        "location": "Remote" if remote else ("; ".join(locations[:3]) or "Global"),
                        "is_remote": "true" if remote else "false",
                        "tags": ",".join(t for t in [category, *terms] if t),
                        "simplify_id": item.get("id") or "",
                    },
                )
            )
        return documents
