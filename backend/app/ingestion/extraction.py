"""Extraction stage: RawDocument -> ExtractedOpportunity, delegated to the AI client."""
from __future__ import annotations

from collections.abc import Iterable

from app.ai import get_ai_client
from app.ai.base import AIClient, ExtractedOpportunity, RawDocument


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
        return candidate

    def extract_many(self, documents: Iterable[RawDocument]) -> list[ExtractedOpportunity]:
        out = []
        for document in documents:
            candidate = self.extract_one(document)
            if candidate is not None:
                out.append(candidate)
        return out
