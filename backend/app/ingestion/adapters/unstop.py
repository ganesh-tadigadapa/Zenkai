"""Unstop public opportunity search.

`unstop.com/api/public/opportunity/search-result` is the JSON endpoint behind
Unstop's own listing pages, and Unstop's robots.txt explicitly allows
`/api/public/*`. Filtered with `oppstatus=open`, it returns only listings whose
registration is open, each with its registration deadline, organiser,
locations, skills and — for internships — the stipend.

Unstop is a marketplace: organisers post their own listings, so the trust
level on the source is lower than an official issuer's, and every record lands
as "Needs verification".
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.feeds import parse_date, strip_markup
from app.models.source import Source

#: Unstop listing type -> Zenkai opportunity type.
TYPE_BY_LISTING = {
    "internships": "internship",
    "hackathons": "hackathon",
    "scholarships": "scholarship",
    "competitions": "competition",
}

PAY_PERIOD = {"monthly": "month", "weekly": "week", "daily": "day", "yearly": "year", "hourly": "hour"}

#: Enough of the organiser's description to read; the full text is one click away.
MAX_DETAILS_CHARS = 1500


def _stipend(job: dict) -> str:
    if (job.get("paid_unpaid") or "").lower() == "unpaid":
        return "Unpaid"
    if not job.get("show_salary") or job.get("not_disclosed"):
        return ""
    low, high = job.get("min_salary"), job.get("max_salary")
    if not low and not high:
        return ""
    amount = f"{low:,}–{high:,}" if low and high and low != high else f"{(high or low):,}"
    currency = "₹" if "rupee" in (job.get("currency") or "") else ""
    period = PAY_PERIOD.get((job.get("pay_in") or "").lower(), "month")
    return f"{currency}{amount} per {period}"


class UnstopAdapter(ApiAdapter):
    url_marker = "unstop.com/api/public/opportunity/search-result"
    name = "unstop"
    complete_listing = True
    #: 30 per page; ten pages is the 300 most recent open listings per type.
    max_pages = 10

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        payload = (json.loads(body) or {}).get("data") or {}
        listings = payload.get("data")
        if not isinstance(listings, list):
            raise ValueError("response carried no listings")

        listing_type = dict(parse_qsl(urlparse(source.url).query)).get("opportunity", "")
        retrieved_at = datetime.now(timezone.utc)
        documents: list[RawDocument] = []
        for record in listings:
            title = (record.get("title") or "").strip()
            url = (record.get("seo_url") or "").strip()
            if not url and record.get("public_url"):
                url = f"https://unstop.com/{record['public_url'].lstrip('/')}"
            if not title or not url:
                continue

            organiser = ((record.get("organisation") or {}).get("name") or "").strip() or "Unstop"
            registration = record.get("regnRequirements") or {}
            deadline = parse_date(registration.get("end_regn_dt") or record.get("end_date"))
            job = record.get("jobDetail") or {}
            cities = [
                c.get("city") for c in record.get("locations") or [] if c.get("city")
            ] or list(job.get("locations") or [])
            if job:
                remote = any(w in (job.get("type") or "").lower() for w in ("remote", "home"))
            else:
                remote = (record.get("region") or "").lower() == "online"
            skills = [
                s.get("skill_name") or s.get("skill")
                for s in record.get("required_skills") or []
                if s.get("skill_name") or s.get("skill")
            ][:8]
            stipend = _stipend(job) if job else ""
            details = strip_markup(record.get("details") or "")[:MAX_DETAILS_CHARS]

            kind = TYPE_BY_LISTING.get(listing_type, "opportunity").replace("_", " ")
            lines = [f"{title} — {kind} listed on Unstop by {organiser}."]
            if deadline:
                lines.append(f"Registration closes {deadline.strftime('%d %B %Y')}.")
            if stipend:
                lines.append(f"Stipend: {stipend}.")
            if remote:
                lines.append("Remote." if job else "Online.")
            elif cities:
                lines.append(f"Location: {', '.join(cities[:3])}.")
            if skills:
                lines.append(f"Skills: {', '.join(skills)}.")
            if details:
                lines.append(f"\n\n{details}")

            documents.append(
                RawDocument(
                    url=url,
                    title=title,
                    text=" ".join(lines).replace(" \n\n", "\n\n"),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": organiser,
                        "adapter": self.name,
                        **({"catalogue": source.category} if source.category else {}),
                        "opportunity_type": TYPE_BY_LISTING.get(listing_type, ""),
                        # isPaid is Unstop's registration-fee flag.
                        "cost_type": "paid" if record.get("isPaid") else "free",
                        "content_type": "application/json",
                        "deadline": deadline.isoformat() if deadline else "",
                        "location": "Remote" if remote else (", ".join(cities[:3]) or "India"),
                        "is_remote": "true" if remote else "false",
                        "skills": ",".join(skills),
                        "tags": ",".join(["Unstop", *([stipend] if stipend else [])]),
                        "unstop_id": str(record.get("id") or ""),
                    },
                )
            )
        return documents

    def next_page_url(self, body: str, current_url: str) -> str | None:
        payload = (json.loads(body) or {}).get("data") or {}
        page, last = payload.get("current_page"), payload.get("last_page")
        if not page or not last or page >= last:
            return None
        parts = urlparse(current_url)
        query = [(k, v) for k, v in parse_qsl(parts.query) if k != "page"] + [("page", str(page + 1))]
        return urlunparse(parts._replace(query=urlencode(query)))
