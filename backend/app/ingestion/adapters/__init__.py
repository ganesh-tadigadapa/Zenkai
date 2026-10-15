from app.ingestion.adapters.base import ApiAdapter
from app.ingestion.adapters.devpost import DevpostAdapter
from app.ingestion.adapters.github_pack import GitHubPackOffersAdapter
from app.ingestion.adapters.microsoft_learn import MicrosoftLearnAdapter
from app.ingestion.adapters.mlh import MLHEventsAdapter
from app.ingestion.adapters.simplify import SimplifyInternshipsAdapter
from app.ingestion.adapters.unstop import UnstopAdapter

REGISTRY: list[ApiAdapter] = [
    MicrosoftLearnAdapter(),
    DevpostAdapter(),
    MLHEventsAdapter(),
    UnstopAdapter(),
    SimplifyInternshipsAdapter(),
    GitHubPackOffersAdapter(),
]


def adapter_for(source) -> ApiAdapter | None:
    for adapter in REGISTRY:
        if adapter.handles(source):
            return adapter
    return None


__all__ = [
    "ApiAdapter",
    "DevpostAdapter",
    "GitHubPackOffersAdapter",
    "MLHEventsAdapter",
    "MicrosoftLearnAdapter",
    "SimplifyInternshipsAdapter",
    "UnstopAdapter",
    "adapter_for",
]
