"""Live discovery: feed parsing, polite fetching, relevance and the connector.

Every test here runs against fixture bodies. The autouse `no_network` guard in
conftest turns an accidental live request into an immediate failure, so none of
these can quietly start depending on a real site being up.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.ingestion.connectors.rss_connector import RSSConnector
from app.ingestion.feeds import FeedParseError, parse_date, parse_feed, strip_markup
from app.ingestion.fetcher import FetchFailed, FetchRefused
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.relevance import assess
from app.models.enums import SourceType
from app.models.opportunity import Opportunity
from app.models.provenance import OpportunityProvenance, RawSourceDocument, SourceCheck
from app.models.source import Source
from tests.conftest import FakeFetcher

RSS_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Opportunities</title>
    <item>
      <title>Summer internship applications open</title>
      <link>https://example.org/intern-2026</link>
      <description>&lt;p&gt;Applications are open for our paid summer internship.
        Open to students; the deadline is published on the programme page.&lt;/p&gt;</description>
      <pubDate>Tue, 10 Feb 2026 09:00:00 +0000</pubDate>
      <guid>https://example.org/intern-2026</guid>
      <category>internships</category>
    </item>
    <item>
      <title>Our database now supports read replicas</title>
      <link>https://example.org/replicas</link>
      <description>The managed database now supports read replicas in all regions.</description>
      <pubDate>Mon, 09 Feb 2026 09:00:00 +0000</pubDate>
    </item>
    <item>
      <title>No link here</title>
      <description>Applications are open for this internship.</description>
    </item>
  </channel>
</rss>
"""

ATOM_BODY = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example Announcements</title>
  <entry>
    <title>Scholarship applications are open</title>
    <link rel="alternate" href="https://example.org/scholarship"/>
    <id>tag:example.org,2026:scholarship</id>
    <published>2026-02-06T16:00:00-08:00</published>
    <summary>Applications are open. Eligibility is listed on the official page.</summary>
    <category term="scholarships"/>
  </entry>
</feed>
"""


def make_source(db, url="https://example.org/feed", **kwargs) -> Source:
    defaults = dict(
        name="Example Feed",
        organization="Example Body",
        url=url,
        source_type=SourceType.RSS.value,
        discovery_method="rss",
        authority="official_organization",
        active=True,
        robots_allowed=True,
        trust_level=5,
    )
    defaults.update(kwargs)
    source = Source(**defaults)
    db.add(source)
    db.flush()
    return source


# --- Parsing ----------------------------------------------------------------

def test_rss_entries_are_parsed_with_their_fields():
    feed = parse_feed(RSS_BODY)
    assert feed.format == "rss"
    assert feed.title == "Example Opportunities"
    assert len(feed.entries) == 3

    first = feed.entries[0]
    assert first.title == "Summer internship applications open"
    assert first.link == "https://example.org/intern-2026"
    assert "paid summer internship" in first.summary
    assert first.published_at == datetime(2026, 2, 10, 9, 0, tzinfo=timezone.utc)
    assert first.categories == ["internships"]


def test_atom_entries_are_parsed_with_their_fields():
    feed = parse_feed(ATOM_BODY)
    assert feed.format == "atom"
    assert len(feed.entries) == 1
    entry = feed.entries[0]
    assert entry.title == "Scholarship applications are open"
    assert entry.link == "https://example.org/scholarship"
    assert entry.published_at is not None
    assert entry.categories == ["scholarships"]


def test_markup_is_stripped_from_summaries():
    assert strip_markup("&lt;p&gt;Hello   <b>world</b>&lt;/p&gt;") == "Hello world"
    assert strip_markup("") == ""


@pytest.mark.parametrize(
    "value",
    ["", "   ", "not a date", None, "32 Foo 2026"],
)
def test_an_unparseable_date_is_none_never_a_guess(value):
    """A feed with a broken date must not be given today's date instead."""
    assert parse_date(value) is None


def test_dates_survive_both_feed_conventions():
    assert parse_date("Tue, 10 Feb 2026 09:00:00 +0000") is not None
    assert parse_date("2026-02-06T16:00:00-08:00") is not None
    assert parse_date("2026-02-06T16:00:00Z") is not None


@pytest.mark.parametrize(
    "body,reason",
    [
        ("", "empty"),
        ("   ", "empty"),
        ("<html><body>Not a feed</body></html>", "unrecognised"),
        ("<rss version='2.0'><oops/></rss>", "channel"),
        ("<rss version='2.0'><channel>", "well-formed"),
    ],
)
def test_a_non_feed_body_raises_rather_than_returning_nothing(body, reason):
    """Empty and broken must stay distinguishable, or the guard cannot work."""
    with pytest.raises(FeedParseError) as exc:
        parse_feed(body)
    assert reason in str(exc.value).lower()


# --- Relevance --------------------------------------------------------------

def test_an_opportunity_announcement_is_accepted():
    verdict = assess("Summer internship applications open", "Applications are open to students.")
    assert verdict.relevant is True
    assert verdict.reasons


def test_a_product_announcement_is_rejected():
    verdict = assess(
        "Amazon ECS Express Mode now supports AWS Graviton workloads",
        "Customers can now run ARM64 workloads with no additional cost.",
    )
    assert verdict.relevant is False
    assert "announcement" in (verdict.rejected_because or "")


def test_supporting_signals_alone_are_not_enough():
    """Stating a price and eligibility describes most documentation pages."""
    verdict = assess("Pricing and eligibility", "This is free and open to everyone.")
    assert verdict.relevant is False


def test_grants_as_a_verb_does_not_count_as_funding():
    """"grants permission" is not a scholarship."""
    verdict = assess("IAM now grants scoped access", "The role grants permission to read.")
    assert verdict.relevant is False


def test_a_senior_job_posting_is_not_a_student_opportunity():
    verdict = assess("Senior Python Engineer, Example Corp", "We are hiring a senior engineer.")
    assert verdict.relevant is False


def test_an_empty_item_is_rejected():
    assert assess("", "").relevant is False


# --- Connector --------------------------------------------------------------

def test_the_connector_yields_one_document_per_linked_entry(db):
    source = make_source(db)
    connector = RSSConnector(fetcher=FakeFetcher({source.url: RSS_BODY}))
    documents = list(connector.fetch(source))

    # The third item has no link, so there is nowhere to send anyone.
    assert len(documents) == 2
    assert documents[0].url == "https://example.org/intern-2026"
    assert documents[0].metadata["organization"] == "Example Body"
    assert documents[0].metadata["feed_format"] == "rss"


def test_the_connector_handles_atom_as_well_as_rss(db):
    source = make_source(db, source_type=SourceType.ATOM.value, discovery_method="atom")
    connector = RSSConnector(fetcher=FakeFetcher({source.url: ATOM_BODY}))
    documents = list(connector.fetch(source))
    assert [d.url for d in documents] == ["https://example.org/scholarship"]


def test_the_connector_refuses_a_source_that_disallows_automation(db):
    source = make_source(db, robots_allowed=False)
    connector = RSSConnector(fetcher=FakeFetcher({source.url: RSS_BODY}))
    with pytest.raises(PermissionError):
        list(connector.fetch(source))


def test_the_connector_refuses_an_inactive_source(db):
    source = make_source(db, active=False)
    connector = RSSConnector(fetcher=FakeFetcher({source.url: RSS_BODY}))
    with pytest.raises(PermissionError):
        list(connector.fetch(source))


def test_a_refusal_from_the_host_is_not_retried(db):
    """A 403 is the provider saying no. It is recorded, not worked around."""
    source = make_source(db)
    fetcher = FakeFetcher({source.url: FetchRefused("HTTP 403 — the source declined this client")})
    connector = RSSConnector(fetcher=fetcher)
    with pytest.raises(FetchRefused):
        list(connector.fetch(source))
    assert fetcher.requested == [source.url]  # asked once, gave up


def test_a_page_that_is_not_a_feed_fails_rather_than_looking_empty(db):
    source = make_source(db)
    connector = RSSConnector(fetcher=FakeFetcher({source.url: "<html>Down for maintenance</html>"}))
    with pytest.raises(FetchFailed):
        list(connector.fetch(source))


# --- End to end -------------------------------------------------------------

def run_once(db, source, body):
    pipeline = IngestionPipeline()
    connector = RSSConnector(fetcher=FakeFetcher({source.url: body}))
    documents = list(connector.fetch(source))
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    return pipeline.process_documents(db, documents, source=source, check=check)


def test_a_feed_becomes_records_without_inventing_anything(db):
    source = make_source(db)
    report = run_once(db, source, RSS_BODY)

    assert report.fetched == 2
    assert report.irrelevant == 1  # the product announcement
    assert report.created == 1

    row = db.scalars(
        __import__("sqlalchemy").select(Opportunity).where(Opportunity.data_origin == "ingested")
    ).first()
    assert row is not None
    # The rules that matter, all at once.
    assert row.verification_status == "needs_review", "discovery may not self-certify"
    assert row.deadline is None, "no deadline was stated, so none may be recorded"
    assert row.cost_type == "unknown", "no cost was stated, so none may be guessed"
    assert row.direct_destination_url is None, "no destination was established"
    assert row.category == "internships"
    assert row.opportunity_type == "internship"


def test_evidence_is_kept_for_what_was_acted_on(db):
    source = make_source(db)
    run_once(db, source, RSS_BODY)

    raw = db.query(RawSourceDocument).all()
    # Only the relevant entry is persisted; the announcement is counted, not kept.
    assert len(raw) == 1
    assert raw[0].source_id == source.id
    assert raw[0].content_hash

    provenance = db.query(OpportunityProvenance).one()
    assert provenance.raw_document_id == raw[0].id


def test_running_twice_creates_nothing_the_second_time(db):
    source = make_source(db)
    run_once(db, source, RSS_BODY)
    second = run_once(db, source, RSS_BODY)

    assert second.created == 0
    assert second.unchanged == 1
    from sqlalchemy import func, select

    assert db.scalar(select(func.count()).select_from(Opportunity)) == 1


def test_an_announcement_only_feed_produces_no_opportunities(db):
    """The case that keeps a vendor release feed out of the catalogue."""
    announcements = RSS_BODY.replace("Summer internship applications open", "Now supports IPv6")
    announcements = announcements.replace(
        "Applications are open for our paid summer internship.", "The service now supports IPv6."
    ).replace("Open to students; the deadline is published on the programme page.", "")
    source = make_source(db)
    report = run_once(db, source, announcements)

    assert report.created == 0
    assert report.irrelevant >= 1


# --- Official-API discovery -------------------------------------------------

MS_CATALOGUE = """{
 "certifications": [
  {"uid": "certification.azure-fundamentals",
   "title": "Microsoft Certified: Azure Fundamentals",
   "subtitle": "<p>As a candidate you have <b>basic</b> knowledge. A discounted voucher may apply in 2019.</p>",
   "url": "https://learn.microsoft.com/credentials/certifications/azure-fundamentals/",
   "certification_type": "fundamentals", "levels": ["beginner"],
   "roles": ["developer", "administrator"], "exams": ["exam.az-900"]},
  {"uid": "certification.azure-ai-fundamentals",
   "title": "Microsoft Certified: Azure AI Fundamentals",
   "subtitle": "<p>Candidates have knowledge of AI workloads.</p>",
   "url": "https://learn.microsoft.com/credentials/certifications/azure-ai-fundamentals/",
   "certification_type": "fundamentals", "levels": ["beginner"],
   "roles": ["ai-engineer"], "exams": []}
 ],
 "exams": [{"uid": "exam.az-900", "display_name": "AZ-900", "title": "Azure Fundamentals"}]
}"""


def api_source(db, **kwargs) -> Source:
    defaults = dict(
        name="Microsoft Learn catalogue",
        organization="Microsoft",
        url="https://learn.microsoft.com/api/catalog/?locale=en-us&type=certifications,exams",
        source_type=SourceType.OFFICIAL_API.value,
        discovery_method="official_api",
        authority="official_issuer",
        active=True,
        robots_allowed=True,
        trust_level=5,
    )
    defaults.update(kwargs)
    source = Source(**defaults)
    db.add(source)
    db.flush()
    return source


def test_the_api_adapter_maps_only_what_the_catalogue_carries(db):
    from app.ingestion.connectors.api_connector import APIConnector

    source = api_source(db)
    connector = APIConnector(fetcher=FakeFetcher({source.url: MS_CATALOGUE}))
    documents = list(connector.fetch(source))

    assert len(documents) == 2
    first = documents[0]
    assert first.url.endswith("/azure-fundamentals/")
    assert first.metadata["credential_kind"] == "fundamentals"
    assert first.metadata["exam_codes"] == "AZ-900"
    # The catalogue publishes none of these, and says so.
    assert "cost" in first.metadata["unpublished_fields"]
    assert "deadline" in first.metadata["unpublished_fields"]


def test_a_source_with_no_adapter_fails_loudly(db):
    from app.ingestion.connectors.api_connector import APIConnector
    from app.ingestion.fetcher import FetchFailed

    source = api_source(db, name="Unknown API", url="https://example.org/api/things")
    connector = APIConnector(fetcher=FakeFetcher({source.url: "{}"}))
    with pytest.raises(FetchFailed, match="no API adapter"):
        list(connector.fetch(source))


def test_a_typed_catalogue_bypasses_the_text_gate_but_a_feed_cannot(db):
    """Relevance by construction is an adapter's claim, not a feed's."""
    from app.ingestion.relevance import assess

    # The catalogue endpoint returns only certifications.
    assert assess("Microsoft Certified: Azure Fundamentals", "", catalogue="certifications").relevant
    # A feed cannot claim a category that is not real.
    assert not assess("Anything at all", "", catalogue="not-a-category").relevant


def test_discovered_certifications_are_never_auto_marked_source_checked(db):
    """An official issuer at maximum trust still may not self-certify."""
    from app.ingestion.connectors.api_connector import APIConnector

    source = api_source(db)
    connector = APIConnector(fetcher=FakeFetcher({source.url: MS_CATALOGUE}))
    documents = list(connector.fetch(source))
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    IngestionPipeline().process_documents(db, documents, source=source, check=check)

    from sqlalchemy import select as sa_select

    rows = db.scalars(sa_select(Opportunity).where(Opportunity.data_origin == "ingested")).all()
    assert rows
    assert {r.verification_status for r in rows} == {"needs_review"}


def test_a_source_that_does_not_publish_a_field_overrides_a_prose_guess(db):
    """"discounted voucher" and "2019" in a description are not cost and deadline."""
    from app.ingestion.connectors.api_connector import APIConnector

    source = api_source(db)
    connector = APIConnector(fetcher=FakeFetcher({source.url: MS_CATALOGUE}))
    documents = list(connector.fetch(source))
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    IngestionPipeline().process_documents(db, documents, source=source, check=check)

    from sqlalchemy import select as sa_select

    rows = db.scalars(sa_select(Opportunity).where(Opportunity.data_origin == "ingested")).all()
    assert all(r.cost_type == "unknown" for r in rows), "a prose keyword became a price"
    assert all(r.deadline is None for r in rows), "a year in prose became a deadline"


def test_credential_facts_are_written_from_the_catalogue(db):
    from app.ingestion.connectors.api_connector import APIConnector
    from app.models.credential import CredentialDetail

    source = api_source(db)
    connector = APIConnector(fetcher=FakeFetcher({source.url: MS_CATALOGUE}))
    documents = list(connector.fetch(source))
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    IngestionPipeline().process_documents(db, documents, source=source, check=check)

    details = db.query(CredentialDetail).all()
    assert len(details) == 2
    by_exam = {d.exam_code: d for d in details}
    assert "AZ-900" in by_exam
    az = by_exam["AZ-900"]
    assert az.credential_type == "professional_certification"
    assert az.experience_level == "beginner"
    assert "azure" in az.specializations
    # Unstated by the catalogue, so left alone.
    assert az.proctored_status == "unknown"
    assert az.assessment_type == "unknown"
    assert az.validity_months is None


def test_two_certifications_differing_by_one_word_are_not_merged(db):
    """"Azure Fundamentals" and "Azure AI Fundamentals" are different exams.

    They once scored 1.0 similarity because the tokeniser dropped words shorter
    than three characters — discarding the only word telling them apart.
    """
    from app.ingestion.connectors.api_connector import APIConnector

    source = api_source(db)
    connector = APIConnector(fetcher=FakeFetcher({source.url: MS_CATALOGUE}))
    documents = list(connector.fetch(source))
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    report = IngestionPipeline().process_documents(db, documents, source=source, check=check)

    assert report.created == 2, "two distinct certifications were merged into one"
    from sqlalchemy import func, select as sa_select

    assert db.scalar(sa_select(func.count()).select_from(Opportunity)) == 2


def test_distinct_official_urls_prevent_a_merge_however_close_the_titles(db):
    from app.ingestion.deduplication import DeduplicationService
    from app.ai.base import ExtractedOpportunity
    from tests.conftest import make_opportunity

    existing = make_opportunity(db, title="Azure Fundamentals Certification")
    existing.application_url = "https://example.org/cert/a"
    db.flush()

    candidate = ExtractedOpportunity(
        title="Azure Fundamentals Certification",
        organization_name=existing.organization.name,
        summary="s",
        description="d",
        application_url="https://example.org/cert/b",
    )
    verdict = DeduplicationService().check(db, candidate)
    assert verdict.is_duplicate is False
    assert "URLs differ" in verdict.reason


def test_one_broken_source_does_not_abort_a_run(db):
    """A cycle with several sources must survive any one of them failing."""
    good = api_source(db, name="Good")
    broken = api_source(db, name="Broken", url="https://example.org/api/nope")

    pipeline = IngestionPipeline()
    reports = [pipeline.run_source(db, s) for s in (broken, good)]

    assert reports[0].errors, "the broken source should report an error"
    # Both attempts are on record, and the failure did not stop the second.
    assert db.query(SourceCheck).count() == 2
    assert broken.consecutive_failures == 1


def test_a_bare_noun_counts_only_in_the_title(db):
    """"AWS Training and Certification" in passing is not a certification."""
    from app.ingestion.relevance import assess

    passing = assess(
        "AWS Builder ID adds multi-factor authentication",
        "AWS Builder Center, AWS Training and Certification and Amazon Quick now offer more.",
    )
    subject = assess("New AWS Certification for AI practitioners", "Registration is open.")
    assert passing.relevant is False
    assert subject.relevant is True


def test_a_closed_verdict_cannot_outlive_the_date_behind_it(db):
    """A year in prose must not mark an available certification as closed.

    EXPIRED is decided by comparing a deadline against today. Where that
    deadline came from a field the source does not publish, it is discarded —
    and the verdict has to go with it, or a description mentioning "Office
    2016" hides a live certification from every student.
    """
    from app.ingestion.connectors.api_connector import APIConnector
    from sqlalchemy import select as sa_select

    catalogue = MS_CATALOGUE.replace(
        "A discounted voucher may apply in 2019.",
        "This certification covers Office 2016 and was updated on 2019-03-01.",
    )
    source = api_source(db)
    connector = APIConnector(fetcher=FakeFetcher({source.url: catalogue}))
    documents = list(connector.fetch(source))
    check = SourceCheck(source_id=source.id)
    db.add(check)
    db.flush()
    IngestionPipeline().process_documents(db, documents, source=source, check=check)

    rows = db.scalars(sa_select(Opportunity).where(Opportunity.data_origin == "ingested")).all()
    assert rows
    assert "expired" not in {r.verification_status for r in rows}
    assert all(r.deadline is None for r in rows)
