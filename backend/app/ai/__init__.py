from __future__ import annotations

from functools import lru_cache

from app.ai.base import AIClient, ExtractedOpportunity, RawDocument
from app.ai.stub_client import StubAIClient
from app.core.config import settings


@lru_cache
def get_ai_client() -> AIClient:
    """Resolve the configured provider.

    Only the stub ships today. Adding a provider means implementing ``AIClient``
    and registering it here — no pipeline changes.
    """
    provider = (settings.AI_PROVIDER or "stub").lower()
    if provider == "stub":
        return StubAIClient()
    raise NotImplementedError(
        f"AI_PROVIDER={provider!r} is not implemented. Implement app.ai.base.AIClient "
        "and register it in app.ai.get_ai_client()."
    )


__all__ = ["AIClient", "ExtractedOpportunity", "RawDocument", "get_ai_client"]
