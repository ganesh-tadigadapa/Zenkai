"""Devpost and MLH adapters, the web connector, and URL-based deduplication.

Fixture bodies only, like the rest of the discovery suite: the shapes below are
trimmed copies of what each provider served on 2026-10-15.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.ingestion.adapters.devpost import submission_deadline
from app.ingestion.connectors.api_connector import APIConnector
from app.ingestion.connectors.web_connector import WebConnector
from app.ingestion.fetcher import FetchFailed
from app.ingestion.pipeline import IngestionPipeline
from app.models.enums import SourceType
from app.models.opportunity import Opportunity
from app.models.provenance import SourceCheck
from app.models.source import Source
from tests.conftest import FakeFetcher, make_opportunity

DEVPOST_URL = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open"


def devpost_page(hackathons, total=2, per_page=9):
    return json.dumps(
        {"hackathons": hackathons, "meta": {"total_count": total, "per_page": per_page}}
    )


HACKATHON = {
    "id": 30992,
    "title": "Build, Ship, Shape: Amazon Developer Hackathon",
    "displayed_location": {"icon": "globe", "location": "Online"},
    "url": "https://amazonappdev2026.devpost.com/",
    "submission_period_dates": "Aug 31 - Oct 23, 2026",
    "themes": [{"id": 6, "name": "Machine Learning/AI"}, {"id": 11, "name": "Productivity"}],
    "prize_amount": "$<span data-currency-value>138,000</span>",
    "organization_name": "Amazon",
    "invite_only": False,
}

MLH_PAGE = """<html><head><title>2027 Season Events</title></head><body>
<script data-page="app" type="application/json">{"component":"SeasonEvents\\/Index","props":{
"upcomingEvents":[
 {"id":"e1","name":"SwampHacks XII","startsAt":"2026-10-16T19:00:00Z","endsAt":"2026-10-18T19:00:00Z",
  "url":"/events/swamphacks-xii/prizes","location":"Gainesville, Florida","formatType":"physical",
  "websiteUrl":"https://swamphacks.com/","region":"AMER","customFields":{"hackathon_focus":[]}},
 {"id":"e2","name":"Global Hack Week","startsAt":"2026-11-02T16:00:00Z","endsAt":"2026-11-08T16:00:00Z",
  "url":"/events/ghw/prizes","location":"Everywhere","formatType":"digital",
  "websiteUrl":"https://ghw.mlh.com/","region":"","customFields":{"hackathon_focus":["Software"]}}
],
"pastEvents":[{"id":"old","name":"Innohacks 4.0","websiteUrl":"https://innohacks.live"}]}}</script>
</body></html>"""

PROGRAMME_PAGE = """<html><head><title>Home | Example Fellowship</title>
<meta name="description" content="A paid fellowship for student developers.">
<style>body { color: red }</style><script>var tracking = 1;</script></head>
<body><nav>Menu Login</nav><h1>Example Fellowship</h1>
<p>Applications are open to students worldwide.</p><footer>Copyright</footer></body></html>"""


def make_source(db, **kwargs) -> Source:
    defaults = dict(
        name="Test source",
        organization="Example",
        url="https://example.org/",
        source_type=SourceType.WEB.value,
        discovery_method="public_webpage",
        authority="official_organization",
        active=True,
        robots_allowed=True,
        trust_level=4,
    )
    defaults.update(kwargs)
    source = Source(**defaults)
    db.add(source)
    db.flush()
    return source


def devpost_source(db) -> Source:
    return make_source(
        db,
        name="Devpost Hackathons",
        organization="Devpost",
        url=DEVPOST_URL,
        source_type=SourceType.OFFICIAL_API.value,
        discovery_method="official_api",
        category="hackathons",
    )


def mlh_source(db) -> Source:
    return make_source(
        db,
        name="MLH Events",
        organization="Major League Hacking",
        url="https://www.mlh.com/seasons/2027/events",
        category="hackathons",
    )


def process(db, source, documents):
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    return IngestionPipeline().process_documents(db, documents, source=source, check=check)


# --- Devpost -----------------------------------------------------------------

@pytest.mark.parametrize(
    "period, expected",
    [
        ("Aug 31 - Oct 23, 2026", (2026, 10, 23)),
        ("Dec 01, 2026 - Jan 15, 2027", (2027, 1, 15)),
        ("Oct 01 - 23, 2026", (2026, 10, 23)),
        ("Nov 01, 2026", (2026, 11, 1)),
    ],
)
def test_the_submission_window_closes_on_its_last_day(period, expected):
    deadline = submission_deadline(period)
    assert (deadline.year, deadline.month, deadline.day) == expected
    assert deadline.tzinfo is not None


@pytest.mark.parametrize("period", [None, "", "Ongoing", "TBD - soon"])
def test_an_unreadable_window_is_no_deadline_rather_than_a_guess(period):
    assert submission_deadline(period) is None


def test_devpost_hackathons_are_mapped_from_the_api(db):
    source = devpost_source(db)
    connector = APIConnector(fetcher=FakeFetcher({DEVPOST_URL: devpost_page([HACKATHON], total=1)}))
    [document] = list(connector.fetch(source))

    assert document.url == "https://amazonappdev2026.devpost.com/"
    assert document.metadata["organization"] == "Amazon"
    assert document.metadata["catalogue"] == "hackathons"
    assert document.metadata["deadline"].startswith("2026-10-23")
    assert document.metadata["is_remote"] == "true"
    assert "$138,000" in document.text
    assert "cost" in document.metadata["unpublished_fields"]


def test_invite_only_hackathons_are_skipped(db):
    source = devpost_source(db)
    closed = dict(HACKATHON, id=1, url="https://private.devpost.com/", invite_only=True)
    connector = APIConnector(fetcher=FakeFetcher({DEVPOST_URL: devpost_page([HACKATHON, closed])}))
    assert [d.url for d in connector.fetch(source)] == [HACKATHON["url"]]


def test_devpost_pages_are_followed_until_the_total_is_reached(db):
    source = devpost_source(db)
    second = dict(HACKATHON, id=2, title="Second Hack", url="https://second.devpost.com/")
    page_two = DEVPOST_URL + "&page=2"
    fetcher = FakeFetcher(
        {
            DEVPOST_URL: devpost_page([HACKATHON], total=2, per_page=1),
            page_two: devpost_page([second], total=2, per_page=1),
        }
    )
    documents = list(APIConnector(fetcher=fetcher).fetch(source))

    assert [d.title for d in documents] == [HACKATHON["title"], "Second Hack"]
    assert fetcher.requested == [DEVPOST_URL, page_two]  # and no third request


def test_a_devpost_hackathon_becomes_a_hackathon_with_its_real_deadline(db):
    source = devpost_source(db)
    connector = APIConnector(fetcher=FakeFetcher({DEVPOST_URL: devpost_page([HACKATHON], total=1)}))
    report = process(db, source, list(connector.fetch(source)))
    assert report.created == 1

    row = db.scalars(select(Opportunity).where(Opportunity.source_id == source.id)).one()
    assert row.category == "hackathons"
    assert row.opportunity_type == "hackathon"
    assert row.deadline.replace(tzinfo=timezone.utc).date() == datetime(2026, 10, 23).date()
    assert row.location == "Online" and row.is_remote is True
    assert row.cost_type == "unknown"  # not stated by the API, so not assumed free
    assert row.tags == ["Machine Learning/AI", "Productivity"]
    assert row.verification_status == "needs_review"


# --- MLH ---------------------------------------------------------------------

def test_mlh_upcoming_events_are_read_from_the_embedded_page_data(db):
    source = mlh_source(db)
    connector = WebConnector(fetcher=FakeFetcher({source.url: MLH_PAGE}))
    documents = list(connector.fetch(source))

    assert [d.title for d in documents] == ["SwampHacks XII", "Global Hack Week"]  # no past events
    swamp, ghw = documents
    assert swamp.url == "https://swamphacks.com/"
    assert swamp.metadata["deadline"].startswith("2026-10-16")
    assert swamp.metadata["location"] == "Gainesville, Florida"
    assert swamp.metadata["is_remote"] == "false"
    assert ghw.metadata["location"] == "Online"
    assert ghw.metadata["event_page"] == "https://www.mlh.com/events/ghw/prizes"


def test_an_mlh_page_without_event_data_fails_rather_than_looking_empty(db):
    source = mlh_source(db)
    connector = WebConnector(fetcher=FakeFetcher({source.url: "<html>Maintenance</html>"}))
    with pytest.raises(FetchFailed):
        list(connector.fetch(source))


# --- Generic pages -----------------------------------------------------------

def test_a_programme_page_becomes_one_document_without_page_chrome(db):
    source = make_source(db, url="https://fellowship.example.org/", category="programs")
    connector = WebConnector(fetcher=FakeFetcher({source.url: PROGRAMME_PAGE}))
    [document] = list(connector.fetch(source))

    assert document.title == "Home | Example Fellowship"
    assert "A paid fellowship for student developers." in document.text
    assert "Applications are open to students worldwide." in document.text
    for chrome in ("color: red", "tracking", "Menu Login", "Copyright"):
        assert chrome not in document.text
    assert document.metadata["catalogue"] == "programs"


def test_the_web_connector_honours_the_compliance_gate(db):
    source = make_source(db, robots_allowed=False)
    connector = WebConnector(fetcher=FakeFetcher({source.url: PROGRAMME_PAGE}))
    with pytest.raises(PermissionError):
        list(connector.fetch(source))


def test_a_page_for_a_curated_record_does_not_duplicate_it(db):
    """Same official URL, different title: one opportunity, not two."""
    curated = make_opportunity(db, title="Example Fellowship", category="programs")
    source = make_source(db, url=curated.application_url, category="programs")
    connector = WebConnector(fetcher=FakeFetcher({source.url: PROGRAMME_PAGE}))
    report = process(db, source, list(connector.fetch(source)))

    assert report.created == 0
    assert db.scalar(select(func.count()).select_from(Opportunity)) == 1
    assert curated.title == "Example Fellowship"  # the curated wording is kept


# --- Registry sync -----------------------------------------------------------

def test_reseeding_carries_registry_edits_into_an_existing_database(db):
    from app.seed.run import seed_sources
    from app.seed.sources import SOURCES

    spec = next(s for s in SOURCES if s["name"] == "Devpost Hackathons")
    stale = make_source(db, name=spec["name"], url="https://devpost.com/api/hackathons", active=False)
    stale.consecutive_failures = 3

    seed_sources(db)

    assert stale.url == spec["url"]
    assert stale.active is True
    assert stale.consecutive_failures == 3  # monitoring state is left alone
