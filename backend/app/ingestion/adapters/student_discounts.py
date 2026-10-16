"""Community list of student developer discounts.

`AchoArnold/discount-for-student-dev` on GitHub keeps a long, actively
maintained list of software, hosting, design tools and learning platforms
that are free or discounted for students. Each entry is one line:

    * [Name](https://provider.example/students) [FREE] - What the offer is.

The README is read from raw.githubusercontent.com, which publishes no robots
rules. Links go to each provider's own student page. As with any third-party
list, records land as "Needs verification", and the offer wording is the
list's, so the provider's page remains the place to confirm it.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.models.source import Source

#: Top-level or second-level bullets only; deeper ones are sub-features.
_ENTRY = re.compile(
    r"^\s{0,3}[-*]\s+\[(?P<name>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)\s*"
    r"\[(?P<tag>[^\]]+)\]\s*[-–:]?\s*(?P<text>.*)$"
)
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")

#: The list's own tags, mapped to Zenkai cost types.
COST_BY_TAG = {
    "FREE": "free_for_students",
    "TEMPORARILY FREE": "free_for_students",
    "CREDIT": "free_for_students",
    "DISCOUNT": "discounted",
}

#: Section headings, mapped to the closest Zenkai type. First match wins.
TYPE_BY_SECTION: tuple[tuple[str, str], ...] = (
    ("hosting", "cloud_credits"),
    ("cloud", "cloud_credits"),
    ("infrastructure", "cloud_credits"),
    ("learning", "learning_platform"),
    ("data science", "learning_platform"),
    ("ide", "developer_tool"),
    ("code", "developer_tool"),
    ("version control", "developer_tool"),
    ("monitoring", "developer_tool"),
    ("testing", "developer_tool"),
    ("database", "developer_tool"),
    ("api", "developer_tool"),
)

MAX_TEXT_CHARS = 400


class StudentDiscountsListAdapter(ApiAdapter):
    url_marker = "AchoArnold/discount-for-student-dev"
    name = "student-discounts"
    complete_listing = True

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        retrieved_at = datetime.now(timezone.utc)
        section = ""
        documents: list[RawDocument] = []
        seen: set[str] = set()

        for line in body.splitlines():
            if line.startswith("## "):
                section = line[3:].strip()
                continue
            match = _ENTRY.match(line)
            if not match:
                continue
            tag = match.group("tag").strip().upper()
            cost = COST_BY_TAG.get(tag)
            if cost is None:
                continue  # a product link styled like a tag, not an offer type
            name = match.group("name").strip()
            url = match.group("url").strip()
            if url in seen:
                continue
            seen.add(url)

            text = _MD_LINK.sub(r"\1", match.group("text")).strip()
            text = re.sub(r"\s+", " ", text)[:MAX_TEXT_CHARS]
            lowered = section.lower()
            kind = "cloud_credits" if tag == "CREDIT" else next(
                (k for needle, k in TYPE_BY_SECTION if needle in lowered), "software"
            )
            title = f"{name} — {'student discount' if cost == 'discounted' else 'free for students'}"

            documents.append(
                RawDocument(
                    url=url,
                    title=title,
                    text=f"{name}: {text}" if text else f"{name} student offer.",
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": name,
                        "adapter": self.name,
                        "catalogue": "tech_benefits",
                        "opportunity_type": kind,
                        "cost_type": cost,
                        "content_type": "text/markdown",
                        # Student offers run while you are a student.
                        "deadline": "",
                        "location": "Online",
                        "is_remote": "true",
                        "tags": ",".join(t for t in ["Student offer", section] if t),
                    },
                )
            )

        if not documents:
            raise ValueError("README carried no student offers")
        return documents
