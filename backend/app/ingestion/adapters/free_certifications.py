"""Community list of free certifications.

`ArslanYM/Free-Certifications` on GitHub (MIT) keeps a table of certification
offers that cost nothing to earn: provider, what is offered, a link to the
provider's own page, and when the offer expires. The README is read from
raw.githubusercontent.com, which publishes no robots rules.

A community list is good for *finding* offers, not for vouching for them, so:

* Rows whose offer has visibly ended are dropped: an expiry date in the past,
  a past year, or "limited time" wording on a list nobody can date.
* Cost is only recorded where the row itself says the offer is free or
  discounted. Otherwise it stays UNKNOWN.
* Every record lands as "Needs verification", like any other non-official
  source, and links go to the provider's page, never to the list.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.models.enums import CredentialType, ExperienceLevel, Specialization
from app.models.source import Source

_LINK = re.compile(r"\[[^\]]*\]\(\s*(https?://[^)\s]+)\s*\)")
_YEAR = re.compile(r"\b(20\d\d)\b")
_DATE_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%d-%b-%Y", "%d-%B-%Y", "%d %B %Y", "%d %b %Y", "%Y-%m-%d")

#: Expiry wording that means the offer has no end date.
_OPEN_ENDED = ("unlimited", "unknown", "unknwon", "ongoing", "none", "no expir", "lifetime", "always", "n/a")

#: Keywords in a row, mapped to specializations. Only clear matches count.
SPECIALIZATION_HINTS: tuple[tuple[str, Specialization], ...] = (
    ("aws", Specialization.AWS),
    ("azure", Specialization.AZURE),
    ("google cloud", Specialization.GOOGLE_CLOUD),
    ("gcp", Specialization.GOOGLE_CLOUD),
    ("oracle cloud", Specialization.CLOUD),
    ("oci", Specialization.CLOUD),
    ("cloud", Specialization.CLOUD),
    ("kubernetes", Specialization.KUBERNETES),
    ("devops", Specialization.DEVOPS),
    ("linux", Specialization.LINUX),
    ("network", Specialization.NETWORKING),
    ("security", Specialization.CYBERSECURITY),
    ("cyber", Specialization.CYBERSECURITY),
    ("python", Specialization.PYTHON),
    ("java ", Specialization.JAVA),
    ("javascript", Specialization.JAVASCRIPT),
    ("machine learning", Specialization.MACHINE_LEARNING),
    ("generative ai", Specialization.GENERATIVE_AI),
    (" ai ", Specialization.AI),
    ("data science", Specialization.DATA_SCIENCE),
    ("analytics", Specialization.DATA_ANALYTICS),
    ("database", Specialization.DATABASES),
    ("sql", Specialization.SQL),
    ("git", Specialization.GIT_GITHUB),
    ("marketing", Specialization.DIGITAL_MARKETING),
    ("salesforce", Specialization.SALESFORCE),
)


def _parse_expiry(text: str) -> datetime | None:
    cleaned = re.sub(r"\s+", " ", text).strip().rstrip(".")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def offer_is_open(expiry: str, now: datetime) -> bool:
    """False when the row's own wording shows the offer has ended."""
    lowered = expiry.strip().lower()
    if not lowered or any(word in lowered for word in _OPEN_ENDED):
        return True
    if "limited" in lowered:
        # "Limited time" on an undated list: there is no way to tell it is
        # still running, and most such rows are years old.
        return False
    parsed = _parse_expiry(expiry)
    if parsed is not None:
        return parsed >= now
    years = [int(y) for y in _YEAR.findall(expiry)]
    if years:
        return max(years) >= now.year
    return True


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


class FreeCertificationsListAdapter(ApiAdapter):
    url_marker = "ArslanYM/Free-Certifications"
    name = "free-certifications"
    complete_listing = True

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        now = datetime.now(timezone.utc)
        retrieved_at = now
        section = ""
        documents: list[RawDocument] = []
        seen: set[tuple[str, str]] = set()
        table_rows = 0

        for line in body.splitlines():
            if line.startswith("## "):
                section = line[3:].strip()
                continue
            if not line.startswith("|") or set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
                continue
            cells = _cells(line)
            if cells and cells[0].lower() == "technology":
                continue  # header row
            table_rows += 1

            link = next((m.group(1) for c in cells if (m := _LINK.search(c))), None)
            if not link or len(cells) < 4:
                continue
            link_index = next(i for i, c in enumerate(cells) if _LINK.search(c))
            expiry = cells[link_index + 1] if link_index + 1 < len(cells) else ""
            if not offer_is_open(expiry, now):
                continue

            # Normal rows are Technology | Provider | Description | Link | Expiration.
            # A few omit a column; fall back to whatever precedes the link.
            before = [c for c in cells[:link_index] if c]
            if len(before) >= 3:
                technology, provider, description = before[0], before[1], " ".join(before[2:])
            elif len(before) == 2:
                technology, provider, description = before[0], before[0], before[1]
            else:
                continue
            description = re.sub(r"\s+", " ", description).strip()
            # Rows pasted from provider pages often lose the space after a
            # full stop ("certification.Gain").
            description = re.sub(r"(?<=[a-z])\.(?=[A-Z][a-z])", ". ", description)
            if 8 <= len(description) <= 90:
                # Name the provider when the description does not, so a
                # title like "Free paths and badges" still says whose.
                named = provider.lower().split()[0] in description.lower()
                title = description if named else f"{provider}: {description}"
            else:
                title = f"{technology} certification — {provider}"
            if (title.lower(), link) in seen:
                continue
            seen.add((title.lower(), link))

            lowered = description.lower()
            if any(w in lowered for w in ("discount", "% off", "voucher", "half price")):
                cost = "discounted"
            elif "free" in lowered and not any(w in lowered for w in ("exam fee", "paid exam", "$", "€", "£")):
                cost = "free"
            else:
                cost = ""
            parsed = _parse_expiry(expiry)

            lines = [f"{title}. Offered by {provider}."]
            if description and description != title:
                lines.append(description)
            if expiry:
                lines.append(f"Offer expiry as listed: {expiry}.")

            documents.append(
                RawDocument(
                    url=link,
                    title=title,
                    text=" ".join(lines),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": provider,
                        "adapter": self.name,
                        "catalogue": "certifications",
                        "opportunity_type": "certification",
                        **({"cost_type": cost} if cost else {}),
                        "unpublished_fields": "proctoring,assessment" + ("" if cost else ",cost"),
                        "content_type": "text/markdown",
                        "deadline": parsed.isoformat() if parsed else "",
                        "location": "Online",
                        "is_remote": "true",
                        "tags": ",".join(t for t in ["Free certification", section, technology] if t),
                        "list_section": section,
                        "technology": technology,
                    },
                )
            )

        if not table_rows:
            raise ValueError("README carried no certification table")
        return documents

    # --- Normalisation helpers, used by the pipeline -----------------------

    @staticmethod
    def credential_type(metadata: dict) -> CredentialType:
        """Only the two kinds a row can state outright; anything else is unknown."""
        text = f"{metadata.get('technology', '')} {metadata.get('list_section', '')}".lower()
        if "badge" in text:
            return CredentialType.SKILL_BADGE
        return CredentialType.UNKNOWN

    @staticmethod
    def experience_level(metadata: dict) -> ExperienceLevel:
        return ExperienceLevel.UNKNOWN

    @staticmethod
    def specializations(metadata: dict, title: str = "") -> list[str]:
        text = f" {title} {metadata.get('technology', '')} {metadata.get('list_section', '')} ".lower()
        seen: list[str] = []
        for needle, specialization in SPECIALIZATION_HINTS:
            if needle in text and specialization.value not in seen:
                seen.append(specialization.value)
        return seen

    @staticmethod
    def exam_code(metadata: dict) -> str | None:
        return None
