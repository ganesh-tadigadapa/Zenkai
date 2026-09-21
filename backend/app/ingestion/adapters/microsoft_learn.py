"""Microsoft Learn catalogue API.

`learn.microsoft.com/api/catalog/` is the public JSON catalogue behind
Microsoft's own certification pages. robots.txt permits it, and it carries the
certifications, their level, the roles they target, and the exam codes that sit
behind them.

Deliberately *not* inferred, because the API does not state it:

* **cost** — every Microsoft exam has a fee in practice, but the catalogue does
  not publish one, so this stays UNKNOWN. Guessing a price nobody published is
  the same mistake whether or not the guess is likely to be right.
* **proctoring and assessment** — likewise unstated, so likewise UNKNOWN.
* **validity** — `renewal_frequency_in_days` is empty on all 151 records, so
  nothing is written.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from app.ai.base import RawDocument
from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.feeds import strip_markup
from app.models.enums import CredentialType, ExperienceLevel, Specialization
from app.models.source import Source

#: Microsoft's `certification_type` values, mapped to what a holder actually
#: has. All of these are credentials awarded on passing an exam, which is a
#: professional certification — unlike a course completion certificate.
CREDENTIAL_TYPE_BY_KIND: dict[str, CredentialType] = {
    "role-based": CredentialType.PROFESSIONAL_CERTIFICATION,
    "fundamentals": CredentialType.PROFESSIONAL_CERTIFICATION,
    "specialty": CredentialType.PROFESSIONAL_CERTIFICATION,
    "business": CredentialType.PROFESSIONAL_CERTIFICATION,
    "mos": CredentialType.PROFESSIONAL_CERTIFICATION,
    "mcsa": CredentialType.PROFESSIONAL_CERTIFICATION,
    "mcsd": CredentialType.PROFESSIONAL_CERTIFICATION,
    "mcse": CredentialType.PROFESSIONAL_CERTIFICATION,
    "mta": CredentialType.PROFESSIONAL_CERTIFICATION,
}

LEVEL_BY_NAME: dict[str, ExperienceLevel] = {
    "beginner": ExperienceLevel.BEGINNER,
    "intermediate": ExperienceLevel.INTERMEDIATE,
    "advanced": ExperienceLevel.ADVANCED,
}

#: Microsoft's role taxonomy, mapped onto Zenkai specializations. Roles with no
#: sensible equivalent are simply dropped rather than forced into one.
SPECIALIZATION_BY_ROLE: dict[str, list[Specialization]] = {
    "ai-engineer": [Specialization.AI, Specialization.MACHINE_LEARNING],
    "ai-edge-engineer": [Specialization.AI, Specialization.IOT],
    "data-analyst": [Specialization.DATA_ANALYTICS],
    "data-engineer": [Specialization.DATA_ENGINEERING],
    "data-scientist": [Specialization.DATA_SCIENCE, Specialization.MACHINE_LEARNING],
    "database-administrator": [Specialization.DATABASES, Specialization.SQL],
    "developer": [Specialization.WEB_DEVELOPMENT],
    "devops-engineer": [Specialization.DEVOPS],
    "identity-access-admin": [Specialization.CYBERSECURITY],
    "network-engineer": [Specialization.NETWORKING],
    "platform-engineer": [Specialization.DEVOPS, Specialization.CLOUD],
    "privacy-manager": [Specialization.CYBERSECURITY],
    "security-engineer": [Specialization.CYBERSECURITY],
    "security-operations-analyst": [Specialization.CYBERSECURITY],
    "solution-architect": [Specialization.SYSTEM_DESIGN, Specialization.CLOUD],
    "administrator": [Specialization.CLOUD],
}

#: Products named in a title imply a platform. Only applied on a clear match.
PLATFORM_HINTS: tuple[tuple[str, Specialization], ...] = (
    ("azure", Specialization.AZURE),
    ("sql server", Specialization.SQL),
    ("power bi", Specialization.DATA_ANALYTICS),
    ("dynamics", Specialization.PRODUCT),
    ("security", Specialization.CYBERSECURITY),
    ("devops", Specialization.DEVOPS),
    ("kubernetes", Specialization.KUBERNETES),
)

_EXAM_UID = re.compile(r"^exam\.(.+)$")


class MicrosoftLearnAdapter(ApiAdapter):
    url_marker = "learn.microsoft.com/api/catalog"
    name = "microsoft-learn"

    def to_documents(self, body: str, source: Source) -> list[RawDocument]:
        payload = json.loads(body)
        certifications = payload.get("certifications") or []
        if not certifications:
            raise ValueError("catalogue response contained no certifications")

        # Exam codes live in a separate array, keyed by uid.
        exam_codes: dict[str, str] = {}
        for exam in payload.get("exams") or []:
            uid = exam.get("uid")
            display = (exam.get("display_name") or "").strip()
            if uid and display:
                exam_codes[uid] = display

        retrieved_at = datetime.now(timezone.utc)
        documents: list[RawDocument] = []

        for record in certifications:
            title = (record.get("title") or "").strip()
            url = (record.get("url") or "").strip()
            if not title or not url:
                continue  # nothing to show, or nowhere to send anyone

            description = strip_markup(record.get("subtitle") or "")
            codes = [
                exam_codes[uid]
                for uid in (record.get("exams") or [])
                if isinstance(uid, str) and uid in exam_codes
            ]

            documents.append(
                RawDocument(
                    url=url,
                    title=title,
                    # The extractor reads text; give it the title and the
                    # official description, nothing embellished.
                    text=f"{title}\n\n{description}".strip(),
                    fetched_at=retrieved_at,
                    source_id=source.id,
                    metadata={
                        "organization": "Microsoft",
                        "adapter": self.name,
                        # This endpoint returns certifications and nothing
                        # else, so relevance is established by construction.
                        "catalogue": "certifications",
                        # The catalogue publishes none of these, so the
                        # extractor's prose heuristics must not fill them in: a
                        # description naming "Office 2019" is not a deadline,
                        # and one mentioning a discount is not the exam price.
                        "unpublished_fields": "cost,deadline,proctoring,assessment",
                        "content_type": "application/json",
                        # Structured facts, passed through for normalisation.
                        "credential_kind": record.get("certification_type") or "",
                        "levels": ",".join(record.get("levels") or []),
                        "roles": ",".join(record.get("roles") or []),
                        "exam_codes": ",".join(codes),
                        "uid": record.get("uid") or "",
                        "last_modified": record.get("last_modified") or "",
                    },
                )
            )
        return documents

    # --- Normalisation helpers, used by the pipeline -----------------------

    @staticmethod
    def credential_type(metadata: dict) -> CredentialType:
        kind = (metadata.get("credential_kind") or "").strip().lower()
        return CREDENTIAL_TYPE_BY_KIND.get(kind, CredentialType.UNKNOWN)

    @staticmethod
    def experience_level(metadata: dict) -> ExperienceLevel:
        """The lowest level stated, since that is the entry point for a student."""
        names = [n.strip().lower() for n in (metadata.get("levels") or "").split(",") if n.strip()]
        order = [ExperienceLevel.BEGINNER, ExperienceLevel.INTERMEDIATE, ExperienceLevel.ADVANCED]
        found = [LEVEL_BY_NAME[n] for n in names if n in LEVEL_BY_NAME]
        for level in order:
            if level in found:
                return level
        return ExperienceLevel.UNKNOWN

    @staticmethod
    def specializations(metadata: dict, title: str = "") -> list[str]:
        values: list[Specialization] = []
        for role in (metadata.get("roles") or "").split(","):
            values.extend(SPECIALIZATION_BY_ROLE.get(role.strip().lower(), []))
        lowered = title.lower()
        for needle, specialization in PLATFORM_HINTS:
            if needle in lowered:
                values.append(specialization)
        # Stable order, no duplicates.
        seen: list[str] = []
        for value in values:
            if value.value not in seen:
                seen.append(value.value)
        return seen

    @staticmethod
    def exam_code(metadata: dict) -> str | None:
        codes = [c.strip() for c in (metadata.get("exam_codes") or "").split(",") if c.strip()]
        # A certification can sit behind several exams; record the first and
        # leave the rest to the detail page rather than inventing a composite.
        return codes[0] if codes else None
