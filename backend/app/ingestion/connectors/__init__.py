from app.ingestion.connectors.api_connector import APIConnector
from app.ingestion.connectors.base import SourceConnector
from app.ingestion.connectors.rss_connector import RSSConnector
from app.ingestion.connectors.web_connector import WebConnector

REGISTRY: list[SourceConnector] = [APIConnector(), RSSConnector(), WebConnector()]


def connector_for(source) -> SourceConnector | None:
    for connector in REGISTRY:
        if connector.can_handle(source):
            return connector
    return None


__all__ = ["APIConnector", "RSSConnector", "SourceConnector", "WebConnector", "connector_for"]
