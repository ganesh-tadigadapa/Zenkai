"""GitHub Student Developer Pack offers page.

`education.github.com/pack/offers` lists every partner offer in the pack — the
tools, credits and courses free to verified students — one card per partner.
robots.txt publishes no rules. One request reads the whole page; partner sites
are never fetched.

Each card becomes one tech benefit: the partner, what it does, and the offer
wording exactly as GitHub states it. A partner that leaves the pack drops off
the page and is retired on the next run.
"""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.feeds import strip_markup
from app.models.source import Source

PAGE = "https://education.github.com/pack/offers"

_CARD_SPLIT = re.compile(r'<div class="pack-offer-card\b')
_NAME = re.compile(r'<h3 id="([^"]+)"[^>]*>(.*?)</h3>', re.S)
_ABOUT = re.compile(r'<h4 class="f5">About[^<]*</h4>\s*<p[^>]*>(.*?)</p>', re.S)
_OFFER = re.compile(r'<h5[^>]*>\s*Offer\s*</h5>\s*<p[^>]*>(.*?)</p>', re.S)
_LABEL = re.compile(r'class="Label">(.*?)</span>', re.S)

#: The pack's own tags, mapped to the closest Zenkai type.
TYPE_BY_TAG = (
    ("cloud", "cloud_credits"),
    ("learn", "learning_platform"),
    ("developer tools", "software"),
    ("design", "software"),
)


class GitHubPackOffersAdapter(ApiAdapter):
    url_marker = "education.github.com/pack/offers"
    name = "github-pack"
    complete_listing = True

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        cards = _CARD_SPLIT.split(body)[1:]
        if not cards:
            raise ValueError("page carried no offer cards")

        retrieved_at = datetime.now(timezone.utc)
        documents: list[RawDocument] = []
        for card in cards:
            name_match = _NAME.search(card)
            if not name_match:
                continue
            anchor = name_match.group(1)
            partner = html.unescape(strip_markup(name_match.group(2)))
            about = _ABOUT.search(card)
            about_text = strip_markup(about.group(1)) if about else ""
            offers = [strip_markup(o) for o in _OFFER.findall(card) if strip_markup(o)]
            tags = sorted({html.unescape(strip_markup(t)) for t in _LABEL.findall(card)})
            if not partner or not offers:
                continue

            lowered = [t.lower() for t in tags]
            kind = next(
                (k for needle, k in TYPE_BY_TAG if any(needle in t for t in lowered)),
                "student_benefit",
            )
            lines = [f"{partner} offer in the GitHub Student Developer Pack, free for verified students."]
            if about_text:
                lines.append(f"{partner}: {about_text}")
            lines.extend(offers)

            documents.append(
                RawDocument(
                    url=f"{PAGE}#{anchor}",
                    title=f"{partner} — GitHub Student Developer Pack",
                    text="\n\n".join(lines),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": partner,
                        "adapter": self.name,
                        "catalogue": "tech_benefits",
                        "opportunity_type": kind,
                        "cost_type": "free_for_students",
                        "content_type": "text/html",
                        # Pack offers run while the partner is in the pack.
                        "deadline": "",
                        "location": "Online",
                        "is_remote": "true",
                        "tags": ",".join(["GitHub Student Pack", *tags]),
                    },
                )
            )
        return documents
