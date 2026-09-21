from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.adapters.microsoft_learn import MicrosoftLearnAdapter

REGISTRY: list[ApiAdapter] = [MicrosoftLearnAdapter()]


def adapter_for(source) -> ApiAdapter | None:
    for adapter in REGISTRY:
        if adapter.handles(source):
            return adapter
    return None


__all__ = ["ApiAdapter", "MicrosoftLearnAdapter", "adapter_for"]
