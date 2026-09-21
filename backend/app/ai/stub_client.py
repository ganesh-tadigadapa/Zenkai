"""Deterministic, dependency-free implementation of :class:`AIClient`.

It uses keyword heuristics and regular expressions — useful for tests and local
development, and honest about being no substitute for a real model. Confidence
scores it returns are capped below the auto-approve threshold on purpose, so
stub-extracted records always land in the human review queue.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.ai.base import AIClient, ExtractedOpportunity, RawDocument
from app.models.enums import Category, CostType

CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.CERTIFICATIONS: ("certification", "certificate", "exam voucher", "credential"),
    Category.INTERNSHIPS: ("internship", "intern ", "co-op", "summer analyst"),
    Category.HACKATHONS: ("hackathon", "hack ", "competition", "contest", "challenge"),
    Category.PROGRAMS: ("fellowship", "program", "ambassador", "cohort", "mentorship"),
    Category.TECH_BENEFITS: ("student pack", "free for students", "credits", "developer plan", "pro plan"),
    Category.SCHOLARSHIPS: ("scholarship", "grant", "bursary", "tuition"),
}

DATE_PATTERNS = (
    r"(\d{4}-\d{2}-\d{2})",
    r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})",
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
)

DATE_FORMATS = ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%B %d %Y")


class StubAIClient(AIClient):
    name = "stub"

    def extract(self, document: RawDocument) -> ExtractedOpportunity | None:
        if not document.text.strip():
            return None
        title = document.title or document.text.strip().splitlines()[0][:200]
        candidate = ExtractedOpportunity(
            title=title.strip(),
            organization_name=document.metadata.get("organization", "Unknown"),
            summary=self.summarize(document.text),
            description=document.text.strip(),
            application_url=document.url,
            source_url=document.url,
            deadline=self.extract_deadline(document.text),
            eligibility=self.extract_eligibility(document.text),
        )
        candidate.category = self.classify(candidate)
        candidate.cost_type = self._cost(document.text)
        candidate.confidence = self.confidence(candidate)
        candidate.notes.append("Extracted by the heuristic stub client; requires human review.")
        return candidate

    def classify(self, candidate: ExtractedOpportunity) -> str:
        haystack = f"{candidate.title} {candidate.summary} {candidate.description}".lower()
        best, best_hits = Category.PROGRAMS, 0
        for category, keywords in CATEGORY_KEYWORDS.items():
            hits = sum(haystack.count(k) for k in keywords)
            if hits > best_hits:
                best, best_hits = category, hits
        return best.value

    def extract_deadline(self, text: str) -> datetime | None:
        window = text
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, window, flags=re.IGNORECASE)
            if not match:
                continue
            raw = match.group(1).replace(",", "")
            for fmt in DATE_FORMATS:
                try:
                    return datetime.strptime(raw, fmt.replace(",", "")).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return None

    def extract_eligibility(self, text: str) -> str | None:
        for line in text.splitlines():
            lowered = line.lower()
            if any(k in lowered for k in ("eligib", "who can apply", "requirement", "must be")):
                return line.strip()[:500]
        return None

    def summarize(self, text: str, max_chars: int = 240) -> str:
        collapsed = " ".join(text.split())
        if len(collapsed) <= max_chars:
            return collapsed
        cut = collapsed[:max_chars]
        return cut[: cut.rfind(" ")] + "…"

    def confidence(self, candidate: ExtractedOpportunity) -> float:
        score = 0.2
        if candidate.deadline:
            score += 0.15
        if candidate.eligibility:
            score += 0.1
        if candidate.category:
            score += 0.1
        if len(candidate.description) > 300:
            score += 0.1
        # Capped below AUTO_APPROVE_CONFIDENCE: heuristics never self-approve.
        return round(min(score, 0.65), 2)

    def _cost(self, text: str) -> str:
        """Cost stated by the text, or UNKNOWN.

        Never defaults to PAID. Silence about price is not evidence of a price,
        and guessing one is exactly the kind of invented fact the catalogue
        must not carry. UNKNOWN surfaces as "Cost not confirmed".
        """
        lowered = text.lower()
        if "free for students" in lowered or "student pack" in lowered:
            return CostType.FREE_FOR_STUDENTS.value
        if "free" in lowered or "no cost" in lowered or "at no charge" in lowered:
            return CostType.FREE.value
        if "discount" in lowered:
            return CostType.DISCOUNTED.value
        if "exam fee" in lowered:
            return CostType.EXAM_FEE.value
        return CostType.UNKNOWN.value
