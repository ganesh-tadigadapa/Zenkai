"""Deduplication: exact fingerprint first, then cheap fuzzy title matching."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import ExtractedOpportunity
from app.models.opportunity import Opportunity, content_fingerprint

#: Near-identical, not merely similar. False merging loses a real opportunity
#: and is far worse than a duplicate a reviewer can collapse by hand.
TITLE_SIMILARITY_THRESHOLD = 0.92


def _tokens(value: str) -> set[str]:
    """Words that carry meaning, including short distinguishing ones.

    A length filter here caused real false merges: "Azure Fundamentals" and
    "Azure AI Fundamentals" scored a perfect 1.0 because "AI" — the only word
    telling them apart — was thrown away. Only single characters and a handful
    of stop words are dropped now.
    """
    stop = {"the", "a", "an", "of", "for", "and", "in", "on", "to", "with"}
    cleaned = value.lower().replace("-", " ").replace(":", " ").replace("(", " ").replace(")", " ")
    return {t for t in cleaned.split() if len(t) > 1 and t not in stop}


def _canonical(url: str | None) -> str:
    """A URL stripped of query and fragment, for comparing identity."""
    if not url:
        return ""
    return url.split("?")[0].split("#")[0].rstrip("/").lower()


def title_similarity(a: str, b: str) -> float:
    """Jaccard overlap on word tokens — no dependencies, good enough as a pre-filter."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class DuplicateVerdict:
    is_duplicate: bool
    existing_id: str | None = None
    reason: str = ""
    similarity: float = 0.0


class DeduplicationService:
    """Decides whether a freshly extracted candidate is already in the database."""

    def check(
        self, db: Session, candidate: ExtractedOpportunity, organization_name: str | None = None
    ) -> DuplicateVerdict:
        org = organization_name or candidate.organization_name
        fingerprint = content_fingerprint(candidate.title, org, candidate.application_url)
        exact = db.scalars(
            select(Opportunity).where(Opportunity.content_hash == fingerprint)
        ).first()
        if exact:
            return DuplicateVerdict(True, exact.id, "identical fingerprint", 1.0)

        # Near-identical title from the same organisation suggests a re-post of
        # one opportunity across sources.
        siblings = db.scalars(
            select(Opportunity)
            .join(Opportunity.organization)
            .where(Opportunity.title.ilike(f"%{candidate.title.split()[0]}%"))
            .limit(50)
        ).all()
        best, best_score = None, 0.0
        for sibling in siblings:
            score = title_similarity(candidate.title, sibling.title)
            if score > best_score:
                best, best_score = sibling, score

        if best and best_score >= TITLE_SIMILARITY_THRESHOLD:
            # Distinct official URLs mean distinct opportunities, whatever the
            # titles look like. A provider's catalogue is full of entries that
            # differ by a word — each with its own page — and merging those
            # silently loses records a student could have taken up.
            candidate_url = _canonical(candidate.application_url)
            existing_url = _canonical(best.application_url)
            if candidate_url and existing_url and candidate_url != existing_url:
                return DuplicateVerdict(
                    False,
                    None,
                    "titles are close but the official URLs differ, so these are "
                    "treated as separate opportunities",
                    round(best_score, 2),
                )
            return DuplicateVerdict(True, best.id, "near-identical title", round(best_score, 2))

        return DuplicateVerdict(False, None, "no match", round(best_score, 2))
