"""Provider-agnostic contracts for the AI stage of the pipeline.

Nothing in the product calls an LLM today. These protocols exist so that the
ingestion workers can be written against a stable interface and a real provider
(Anthropic, OpenAI, a local model) can be dropped in behind ``get_ai_client()``
without touching the pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass
class RawDocument:
    """Whatever a connector fetched, before it means anything."""

    url: str
    title: str | None = None
    text: str = ""
    html: str | None = None
    fetched_at: datetime | None = None
    source_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedOpportunity:
    """Structured candidate produced from a RawDocument."""

    title: str
    organization_name: str
    summary: str
    description: str
    category: str | None = None
    opportunity_type: str | None = None
    eligibility: str | None = None
    deadline: datetime | None = None
    cost_type: str | None = None
    location: str | None = None
    is_remote: bool | None = None
    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    application_url: str | None = None
    source_url: str | None = None
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)
    #: Structured facts the source carried, passed through untouched for
    #: normalisation. Never invented — only what an adapter actually read.
    provider_metadata: dict = field(default_factory=dict)


@runtime_checkable
class AIClient(Protocol):
    """The six AI operations the pipeline needs."""

    def extract(self, document: RawDocument) -> ExtractedOpportunity | None: ...

    def classify(self, candidate: ExtractedOpportunity) -> str: ...

    def extract_deadline(self, text: str) -> datetime | None: ...

    def extract_eligibility(self, text: str) -> str | None: ...

    def summarize(self, text: str, max_chars: int = 240) -> str: ...

    def confidence(self, candidate: ExtractedOpportunity) -> float: ...
