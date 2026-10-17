"""Keeping discovered records current: changes, withdrawals and deadlines.

Plus the Unstop, SimplifyJobs and GitHub Student Pack adapters. Fixture bodies
only — trimmed copies of what each provider served on 2026-10-15.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.ingestion.connectors.api_connector import APIConnector
from app.ingestion.connectors.web_connector import WebConnector
from app.ingestion.fetcher import FetchFailed
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.relevance import assess
from app.models.enums import SourceType
from app.models.opportunity import Opportunity
from app.models.provenance import OpportunityProvenance
from app.models.source import Source
from app.services.opportunity_service import expire_passed_deadlines
from tests.conftest import FakeFetcher, make_opportunity

DEVPOST_URL = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open"


def hackathon(n: int, period: str = "Aug 31 - Oct 23, 2030") -> dict:
    return {
        "id": n,
        "title": f"Hack Number {n}",
        "displayed_location": {"location": "Online"},
        "url": f"https://hack{n}.devpost.com/",
        "submission_period_dates": period,
        "themes": [],
        "prize_amount": "",
        "organization_name": "Example",
        "invite_only": False,
    }


def devpost_body(hackathons) -> str:
    return json.dumps(
        {"hackathons": hackathons, "meta": {"total_count": len(hackathons), "per_page": 50}}
    )


def make_source(db, **kwargs) -> Source:
    defaults = dict(
        name="Devpost Hackathons",
        organization="Devpost",
        url=DEVPOST_URL,
        source_type=SourceType.OFFICIAL_API.value,
        discovery_method="official_api",
        authority="established_platform",
        category="hackathons",
        active=True,
        robots_allowed=True,
        trust_level=4,
    )
    defaults.update(kwargs)
    source = Source(**defaults)
    db.add(source)
    db.flush()
    return source


def run(db, source, body):
    """One discovery run of `source` serving `body`."""
    pipeline = IngestionPipeline()
    pipeline_connector = APIConnector(fetcher=FakeFetcher({source.url: body}))
    # run_source picks its own connector; swap in the fixture-backed one.
    import app.ingestion.pipeline as pipeline_module

    original = pipeline_module.connector_for
    pipeline_module.connector_for = lambda _source: pipeline_connector
    try:
        return pipeline.run_source(db, source)
    finally:
        pipeline_module.connector_for = original


def by_url(db, url) -> Opportunity:
    return db.scalars(select(Opportunity).where(Opportunity.application_url == url)).one()


def aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


# --- Changes to records a source already published --------------------------

def test_an_extended_deadline_is_applied_to_the_record(db):
    source = make_source(db)
    run(db, source, devpost_body([hackathon(1, "Aug 31 - Oct 23, 2030")]))

    report = run(db, source, devpost_body([hackathon(1, "Aug 31 - Nov 30, 2030")]))

    assert report.updated == 1
    assert aware(by_url(db, "https://hack1.devpost.com/").deadline).date() == datetime(2030, 11, 30).date()


def test_a_record_closed_and_then_relisted_is_reopened(db):
    source = make_source(db)
    run(db, source, devpost_body([hackathon(1)]))
    row = by_url(db, "https://hack1.devpost.com/")
    row.verification_status = "expired"
    db.flush()

    run(db, source, devpost_body([hackathon(1)]))

    assert row.verification_status == "needs_review"


def test_another_source_cannot_overwrite_a_curated_record(db):
    curated = make_opportunity(db, title="Curated Hack", category="hackathons")
    curated.application_url = "https://hack1.devpost.com/"
    original_summary = curated.summary
    db.flush()
    source = make_source(db)

    run(db, source, devpost_body([hackathon(1, "Aug 31 - Dec 31, 2030")]))

    assert curated.summary == original_summary
    assert curated.verification_status == "curated"
    # ...but what the source said is kept for a reviewer.
    assert db.scalars(
        select(OpportunityProvenance).where(OpportunityProvenance.opportunity_id == curated.id)
    ).first()


# --- Withdrawals ---------------------------------------------------------------

def test_a_record_dropped_from_a_complete_listing_is_closed(db):
    source = make_source(db)
    run(db, source, devpost_body([hackathon(n) for n in range(1, 6)]))

    report = run(db, source, devpost_body([hackathon(n) for n in range(1, 5)]))

    assert report.removed == 1
    assert by_url(db, "https://hack5.devpost.com/").verification_status == "expired"
    assert by_url(db, "https://hack1.devpost.com/").verification_status == "needs_review"
    kinds = db.scalars(select(OpportunityProvenance.change_kind)).all()
    assert "removed" in kinds


def test_an_outage_closes_nothing(db):
    source = make_source(db)
    run(db, source, devpost_body([hackathon(n) for n in range(1, 6)]))

    report = run(db, source, devpost_body([hackathon(1)]))  # 1 of 5: a partial failure

    assert report.blocked_reason
    assert report.removed == 0
    assert by_url(db, "https://hack5.devpost.com/").verification_status == "needs_review"


def test_a_feed_dropping_an_entry_closes_nothing(db):
    """A feed shows its latest N entries; scrolling off it means nothing."""
    from app.ingestion.connectors.rss_connector import RSSConnector

    feed = """<?xml version="1.0"?><rss version="2.0"><channel><title>F</title>{items}</channel></rss>"""
    item = (
        "<item><title>Scholarship {n} applications are open</title>"
        "<link>https://example.org/s{n}</link><description>Apply now.</description></item>"
    )
    source = make_source(
        db, name="Feed", url="https://example.org/feed", source_type="rss", discovery_method="rss",
        category=None,
    )
    pipeline = IngestionPipeline()
    import app.ingestion.pipeline as pipeline_module

    original = pipeline_module.connector_for
    try:
        for count in (5, 4):
            body = feed.format(items="".join(item.format(n=n) for n in range(1, count + 1)))
            connector = RSSConnector(fetcher=FakeFetcher({source.url: body}))
            pipeline_module.connector_for = lambda _s, c=connector: c
            report = pipeline.run_source(db, source)
    finally:
        pipeline_module.connector_for = original

    assert report.removed == 0
    assert by_url(db, "https://example.org/s5").verification_status == "needs_review"


def test_a_capped_listing_closes_nothing(db):
    """Paging stopped early, so the listing is a slice, not the whole."""
    page = lambda items, total: json.dumps(  # noqa: E731
        {"hackathons": items, "meta": {"total_count": total, "per_page": 1}}
    )
    source = make_source(db)
    run(db, source, devpost_body([hackathon(n) for n in range(1, 4)]))

    second = DEVPOST_URL + "&page=2"
    fetcher = FakeFetcher(
        {DEVPOST_URL: page([hackathon(1)], 3), second: FetchFailed("ReadTimeout")}
    )
    documents = list(APIConnector(fetcher=fetcher).fetch(source))

    assert [d.title for d in documents] == ["Hack Number 1"]  # page one is kept
    assert documents[0].metadata["listing_truncated"] == "true"


# --- Deadlines ---------------------------------------------------------------

def test_passed_deadlines_are_closed_across_every_category(db):
    now = datetime.now(timezone.utc)
    rows = [
        make_opportunity(db, title=f"Past {category}", category=category, deadline_days=None)
        for category in ("internships", "scholarships", "hackathons", "certifications")
    ]
    for row in rows:
        row.deadline = now - timedelta(days=1)
    future = make_opportunity(db, title="Future", category="programs", deadline_days=10)
    db.flush()

    assert expire_passed_deadlines(db) == 4
    assert {r.verification_status for r in rows} == {"expired"}
    assert future.verification_status == "curated"


# --- Unstop --------------------------------------------------------------------

UNSTOP_URL = (
    "https://unstop.com/api/public/opportunity/search-result"
    "?opportunity=internships&oppstatus=open&per_page=30"
)
UNSTOP_INTERNSHIP = {
    "id": 1770678,
    "title": "HR Internship",
    "seo_url": "https://unstop.com/internships/hr-internship-orvionar-tech-solutions-1770678",
    "end_date": "2026-11-01T00:00:00+05:30",
    "region": "online",
    "isPaid": False,
    "organisation": {"name": "Orvionar Tech Solutions"},
    "regnRequirements": {"end_regn_dt": "2026-10-26T00:00:00+05:30"},
    "locations": [{"city": "Bangalore"}],
    "required_skills": [{"skill_name": "Talent Sourcing"}, {"skill_name": "Resume Screening"}],
    "jobDetail": {
        "type": "in_office", "paid_unpaid": "paid", "show_salary": 1, "not_disclosed": False,
        "min_salary": 10000, "max_salary": 14000, "currency": "fa-rupee", "pay_in": "monthly",
    },
    "details": "<h3>Responsibilities</h3><ul><li>Assist with sourcing.</li></ul>",
}


def unstop_body(records, page=1, last=1) -> str:
    return json.dumps({"data": {"data": records, "current_page": page, "last_page": last}})


def test_unstop_internships_carry_deadline_stipend_and_skills(db):
    source = make_source(db, name="Unstop internships", url=UNSTOP_URL, category="internships")
    [document] = list(APIConnector(fetcher=FakeFetcher({UNSTOP_URL: unstop_body([UNSTOP_INTERNSHIP])})).fetch(source))

    assert datetime.fromisoformat(document.metadata["deadline"]) == datetime(
        2026, 10, 25, 18, 30, tzinfo=timezone.utc
    )  # midnight, 26 October, IST
    assert document.metadata["location"] == "Bangalore"
    assert document.metadata["is_remote"] == "false"  # registration online, work in office
    assert document.metadata["cost_type"] == "free"
    assert document.metadata["skills"] == "Talent Sourcing,Resume Screening"
    assert "₹10,000–14,000 per month" in document.text
    assert "Assist with sourcing." in document.text


def test_unstop_pages_are_followed_to_the_last(db):
    source = make_source(db, name="Unstop internships", url=UNSTOP_URL, category="internships")
    page_two = UNSTOP_URL + "&page=2"
    second = dict(UNSTOP_INTERNSHIP, id=2, title="Data Internship", seo_url="https://unstop.com/i/2")
    fetcher = FakeFetcher(
        {UNSTOP_URL: unstop_body([UNSTOP_INTERNSHIP], 1, 2), page_two: unstop_body([second], 2, 2)}
    )
    documents = list(APIConnector(fetcher=fetcher).fetch(source))
    assert [d.title for d in documents] == ["HR Internship", "Data Internship"]


# --- SimplifyJobs --------------------------------------------------------------

SIMPLIFY_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json"
)


def test_only_active_visible_simplify_postings_are_read_newest_first(db):
    now = int(time.time())
    listings = [
        {"title": "SWE Intern", "company_name": "Old Co", "url": "https://old.example/apply",
         "active": True, "is_visible": True, "date_posted": now - 86400 * 30, "locations": ["Remote in USA"],
         "terms": ["Summer 2027"], "category": "Software"},
        {"title": "ML Intern", "company_name": "New Co", "url": "https://new.example/apply",
         "active": True, "is_visible": True, "date_posted": now, "locations": ["London, UK"],
         "terms": ["N/A"], "category": "AI/ML/Data"},
        {"title": "Closed Intern", "company_name": "Gone Co", "url": "https://gone.example/apply",
         "active": False, "is_visible": True, "date_posted": now},
        {"title": "Hidden Intern", "company_name": "Hid Co", "url": "https://hid.example/apply",
         "active": True, "is_visible": False, "date_posted": now},
    ]
    source = make_source(db, name="SimplifyJobs internships", url=SIMPLIFY_URL, category="internships")
    documents = list(APIConnector(fetcher=FakeFetcher({SIMPLIFY_URL: json.dumps(listings)})).fetch(source))

    assert [d.title for d in documents] == ["ML Intern — New Co", "SWE Intern — Old Co"]
    assert documents[1].metadata["is_remote"] == "true"
    assert documents[1].metadata["tags"] == "Software,Summer 2027"
    assert documents[0].metadata["deadline"] == ""


# --- GitHub Student Pack -----------------------------------------------------------

PACK_PAGE = """<html><body>
<div class="pack-offer-card border rounded-2 p-3" > <h3 id="jetbrains" class="sr-only">JetBrains</h3>
<h4 class="f5">About JetBrains</h4> <p class="mb-3">Professional desktop IDEs.</p>
<h5 class="f5 mb-1">Offer</h5> <p style="margin-bottom: 12px;">Free subscription to all IDEs while a student.</p>
<ul><li><span data-view-component="true" class="Label">Developer tools</span></li></ul></div>
<div class="pack-offer-card border rounded-2 p-3" > <h3 id="azure" class="sr-only">Microsoft Azure</h3>
<h4 class="f5">About Microsoft Azure</h4> <p class="mb-3">Cloud services.</p>
<h5 class="f5 mb-1">Offer</h5> <p>$100 in Azure credits.</p>
<ul><li><span data-view-component="true" class="Label">Cloud</span></li></ul></div>
</body></html>"""


def test_each_pack_partner_becomes_a_student_benefit(db):
    source = make_source(
        db, name="GitHub Student Pack offers", url="https://education.github.com/pack/offers",
        source_type=SourceType.WEB.value, discovery_method="public_webpage", category="tech_benefits",
    )
    documents = list(WebConnector(fetcher=FakeFetcher({source.url: PACK_PAGE})).fetch(source))

    assert [d.title for d in documents] == [
        "JetBrains — GitHub Student Developer Pack",
        "Microsoft Azure — GitHub Student Developer Pack",
    ]
    jetbrains, azure = documents
    assert jetbrains.url == "https://education.github.com/pack/offers#jetbrains"
    assert "Free subscription to all IDEs" in jetbrains.text
    assert jetbrains.metadata["opportunity_type"] == "software"
    assert azure.metadata["opportunity_type"] == "cloud_credits"
    assert azure.metadata["cost_type"] == "free_for_students"


# --- Relevance -------------------------------------------------------------------

@pytest.mark.parametrize(
    "title",
    ["18 Global Opportunities for Women and Girls Currently Open", "Top 10 Fully Funded Scholarships"],
)
def test_roundup_posts_are_not_opportunities(title):
    assert not assess(title, "Applications are open. Deadline November 2026.").relevant
