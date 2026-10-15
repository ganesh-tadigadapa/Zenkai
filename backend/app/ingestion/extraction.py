"""Extraction stage: RawDocument -> ExtractedOpportunity, delegated to the AI client."""
from __future__ import annotations

from collections.abc import Iterable

from app.ai import get_ai_client
from app.ai.base import AIClient, ExtractedOpportunity, RawDocument
from app.ingestion.feeds import parse_date
from app.models.enums import Category, CostType, OpportunityType

_CATEGORIES = {c.value for c in Category}
_TYPES = {t.value for t in OpportunityType}
_COSTS = {c.value for c in CostType}


def apply_structured_facts(candidate: ExtractedOpportunity, metadata: dict) -> None:
    """Let facts a source stated as data win over guesses read from prose.

    Only keys the connector actually set are applied. A present-but-empty
    ``deadline`` is a statement too: the source carries the field and it could
    not be read, so a date the text heuristics found elsewhere is discarded.
    """
    if metadata.get("catalogue") in _CATEGORIES:
        candidate.category = metadata["catalogue"]
    if metadata.get("opportunity_type") in _TYPES:
        candidate.opportunity_type = metadata["opportunity_type"]
    if "deadline" in metadata:
        candidate.deadline = parse_date(metadata["deadline"])
    if metadata.get("location"):
        candidate.location = metadata["location"]
    if metadata.get("is_remote") in ("true", "false"):
        candidate.is_remote = metadata["is_remote"] == "true"
    if metadata.get("cost_type") in _COSTS:
        candidate.cost_type = metadata["cost_type"]
    tags = [t.strip() for t in (metadata.get("tags") or "").split(",") if t.strip()]
    if tags:
        candidate.tags = tags
    skills = [s.strip() for s in (metadata.get("skills") or "").split(",") if s.strip()]
    if skills:
        candidate.skills = skills


class OpportunityExtractor:
    def __init__(self, client: AIClient | None = None) -> None:
        self.client = client or get_ai_client()

    def extract_one(self, document: RawDocument) -> ExtractedOpportunity | None:
        candidate = self.client.extract(document)
        if candidate is None:
            return None
        if not candidate.category:
            candidate.category = self.client.classify(candidate)
        if candidate.deadline is None:
            candidate.deadline = self.client.extract_deadline(document.text)
        if candidate.eligibility is None:
            candidate.eligibility = self.client.extract_eligibility(document.text)
        candidate.confidence = self.client.confidence(candidate)
        # Carry the source's structured facts forward. The extractor reads
        # prose; an adapter may already know the level, roles and exam code.
        candidate.provider_metadata = dict(document.metadata or {})
        apply_structured_facts(candidate, candidate.provider_metadata)
        return candidate

    def extract_many(self, documents: Iterable[RawDocument]) -> list[ExtractedOpportunity]:
        out = []
        for document in documents:
            candidate = self.extract_one(document)
            if candidate is not None:
                out.append(candidate)
        return out
