"""Automated verification checks that run before a human sees a candidate.

These checks establish *plausibility*, never truth. Anything below
``AUTO_APPROVE_CONFIDENCE`` is routed to the human review queue, and the product
never presents a record as checked on the strength of automation alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.ai.base import ExtractedOpportunity
from app.models.enums import VerificationStatus

# Nothing in this build can reach it — it exists for a future connector whose
# source is an official API with a trust_level of 5. Even then the best an
# automated check can assert is SOURCE_CHECKED, never a human sign-off.
AUTO_APPROVE_CONFIDENCE = 0.95


@dataclass
class VerificationResult:
    status: VerificationStatus
    confidence: float
    checks: dict[str, bool] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


class VerificationService:
    def check(
        self, candidate: ExtractedOpportunity, *, source_trust: int = 3, now: datetime | None = None
    ) -> VerificationResult:
        now = now or datetime.now(timezone.utc)
        checks: dict[str, bool] = {}
        issues: list[str] = []

        url = candidate.application_url or candidate.source_url or ""
        parsed = urlparse(url)
        checks["has_https_url"] = parsed.scheme == "https"
        if not checks["has_https_url"]:
            issues.append("Application URL is missing or not HTTPS.")

        checks["has_title"] = bool(candidate.title and len(candidate.title) > 5)
        checks["has_description"] = bool(candidate.description and len(candidate.description) > 80)
        if not checks["has_description"]:
            issues.append("Description is too short to review.")

        checks["has_category"] = bool(candidate.category)
        checks["has_eligibility"] = bool(candidate.eligibility)
        if not checks["has_eligibility"]:
            issues.append("No eligibility statement found.")

        deadline_ok = True
        if candidate.deadline:
            deadline = candidate.deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            deadline_ok = deadline > now
            if not deadline_ok:
                issues.append("Extracted deadline is in the past.")
        checks["deadline_in_future"] = deadline_ok

        passed = sum(1 for v in checks.values() if v)
        base = passed / len(checks)
        trust_bonus = (source_trust - 3) * 0.05  # -0.10 .. +0.10
        confidence = round(max(0.0, min(1.0, base * 0.9 + trust_bonus)), 2)

        if candidate.deadline and not deadline_ok:
            status = VerificationStatus.EXPIRED
        elif confidence >= AUTO_APPROVE_CONFIDENCE:
            status = VerificationStatus.SOURCE_CHECKED
        else:
            status = VerificationStatus.NEEDS_REVIEW

        return VerificationResult(status=status, confidence=confidence, checks=checks, issues=issues)
