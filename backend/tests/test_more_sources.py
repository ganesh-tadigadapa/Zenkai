"""Applied Skills, Unstop competitions, and the two community lists."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.ingestion.adapters.free_certifications import offer_is_open
from app.ingestion.connectors.api_connector import APIConnector
from app.models.credential import CredentialDetail
from app.models.enums import SourceType
from app.models.opportunity import Opportunity
from tests.conftest import FakeFetcher
from tests.test_live_sources import make_source, process

NOW = datetime(2026, 10, 16, tzinfo=timezone.utc)


def api_source(db, **kwargs):
    defaults = dict(
        source_type=SourceType.OFFICIAL_API.value,
        discovery_method="official_api",
    )
    defaults.update(kwargs)
    return make_source(db, **defaults)


def read(source, body):
    return list(APIConnector(fetcher=FakeFetcher({source.url: body})).fetch(source))


# --- Microsoft Learn Applied Skills -----------------------------------------

APPLIED_URL = "https://learn.microsoft.com/api/catalog/?locale=en-us&type=appliedSkills"
APPLIED_SKILL = {
    "uid": "applied-skill.secure-storage",
    "url": "https://learn.microsoft.com/en-us/credentials/applied-skills/secure-storage/",
    "title": "Microsoft Applied Skills: Secure storage for Azure Files",
    "summary": "<p>Learners demonstrate the ability to secure Azure storage.</p>",
    "levels": ["intermediate"],
    "roles": ["security-engineer"],
    "last_modified": "2025-06-24T19:57:00+00:00",
}


def applied_source(db):
    return api_source(
        db, name="Microsoft Learn Applied Skills", organization="Microsoft",
        url=APPLIED_URL, category="certifications", authority="official_issuer",
    )


def test_applied_skills_are_read_from_their_own_collection(db):
    source = applied_source(db)
    [document] = read(source, json.dumps({"appliedSkills": [APPLIED_SKILL]}))

    assert document.title == APPLIED_SKILL["title"]
    assert "secure Azure storage" in document.text
    assert "<p>" not in document.text
    assert document.metadata["credential_kind"] == "applied-skill"
    assert "cost" in document.metadata["unpublished_fields"]


def test_an_applied_skill_is_recorded_as_a_micro_credential(db):
    source = applied_source(db)
    process(db, source, read(source, json.dumps({"appliedSkills": [APPLIED_SKILL]})))

    row = db.scalars(select(Opportunity).where(Opportunity.source_id == source.id)).one()
    detail = db.scalars(select(CredentialDetail).where(CredentialDetail.opportunity_id == row.id)).one()
    assert row.category == "certifications"
    assert row.cost_type == "unknown"  # the API does not publish a price
    assert detail.credential_type == "micro_credential"
    assert detail.experience_level == "intermediate"
    assert "cybersecurity" in detail.specializations


def test_a_catalogue_with_neither_collection_fails_loudly(db):
    from app.ingestion.fetcher import FetchFailed

    source = applied_source(db)
    with pytest.raises(FetchFailed):
        read(source, json.dumps({"appliedSkills": []}))


# --- Unstop competitions ----------------------------------------------------

UNSTOP_COMPETITIONS = (
    "https://unstop.com/api/public/opportunity/search-result"
    "?opportunity=competitions&oppstatus=open&per_page=30"
)


def test_unstop_competitions_land_under_hackathons_and_competitions(db):
    source = api_source(
        db, name="Unstop competitions", organization="Unstop", url=UNSTOP_COMPETITIONS,
        category="hackathons", authority="established_platform",
    )
    record = {
        "id": 7,
        "title": "Case Study Challenge 2026",
        "seo_url": "https://unstop.com/competitions/case-study-challenge-2026-7",
        "organisation": {"name": "IIM Example"},
        "regnRequirements": {"end_regn_dt": "2026-11-20T23:59:00+05:30"},
        "region": "online",
        "isPaid": False,
    }
    body = json.dumps({"data": {"data": [record], "current_page": 1, "last_page": 1}})
    [document] = read(source, body)
    assert document.metadata["opportunity_type"] == "competition"
    assert document.metadata["catalogue"] == "hackathons"

    process(db, source, [document])
    row = db.scalars(select(Opportunity).where(Opportunity.source_id == source.id)).one()
    assert row.category == "hackathons"
    assert row.opportunity_type == "competition"
    assert row.is_remote is True


# --- Free certifications list -----------------------------------------------

FREE_CERTS_URL = "https://raw.githubusercontent.com/ArslanYM/Free-Certifications/main/README.md"
FREE_CERTS_README = """# Free-Certifications

| Technology | Provider | Description | Link | Expiration |
| --- | --- | --- | --- | --- |
| OCI | Oracle | Oracle Cloud Infrastructure Foundations Associate | [Link](https://education.oracle.com/oci-foundations) | Unlimited |
| Gitlab Certification | Gitlab | Free certification paths and badges | [Link](https://about.gitlab.com/learn/) | Unknown |
| Nutanix Certification | Nutanix | Free certification exams until New year | [Link](https://next.nutanix.com/free) | January 31, 2022 |
| Azure | Microsoft | Free AZ-900 exam after a virtual training day | [Link](https://www.microsoft.com/training-days) | Limited Time |
| Cloud | Example | Discounted exam voucher for students | [Link](https://example.com/voucher) | 31-Dec-2099 |

## Security

| Technology | Provider | Description | Link | Expiration |
| --- | --- | --- | --- | --- |
| Cybersecurity | Fortinet | Free NSE 1 and NSE 2 cybersecurity courses | [Link](https://training.fortinet.com/) | Unlimited |
"""


def free_certs_source(db):
    return api_source(
        db, name="Free Certifications list", organization="ArslanYM/Free-Certifications",
        url=FREE_CERTS_URL, category="certifications", authority="other_reputable_source",
        trust_level=3,
    )


@pytest.mark.parametrize(
    "expiry, still_open",
    [
        ("Unlimited", True),
        ("Unknown", True),
        ("", True),
        ("January 31, 2022", False),
        ("01-Jan-2025", False),
        ("31-Dec-2027", True),
        ("2023", False),
        ("Limited Time", False),
    ],
)
def test_ended_offers_are_recognised_from_the_listed_expiry(expiry, still_open):
    assert offer_is_open(expiry, NOW) is still_open


def test_only_offers_that_have_not_ended_are_read(db):
    documents = read(free_certs_source(db), FREE_CERTS_README)
    urls = [d.url for d in documents]

    assert "https://next.nutanix.com/free" not in urls  # expired in 2022
    assert "https://www.microsoft.com/training-days" not in urls  # undated "limited time"
    assert urls == [
        "https://education.oracle.com/oci-foundations",
        "https://about.gitlab.com/learn/",
        "https://example.com/voucher",
        "https://training.fortinet.com/",
    ]


def test_cost_is_recorded_only_where_the_row_states_it(db):
    by_url = {d.url: d for d in read(free_certs_source(db), FREE_CERTS_README)}

    assert by_url["https://about.gitlab.com/learn/"].metadata["cost_type"] == "free"
    assert by_url["https://example.com/voucher"].metadata["cost_type"] == "discounted"
    oracle = by_url["https://education.oracle.com/oci-foundations"]
    assert "cost_type" not in oracle.metadata  # the row never says it is free
    assert "cost" in oracle.metadata["unpublished_fields"]


def test_a_listed_expiry_date_becomes_the_deadline(db):
    by_url = {d.url: d for d in read(free_certs_source(db), FREE_CERTS_README)}
    assert by_url["https://example.com/voucher"].metadata["deadline"].startswith("2099-12-31")
    assert by_url["https://about.gitlab.com/learn/"].metadata["deadline"] == ""


def test_titles_name_the_provider_and_sections_become_tags(db):
    by_url = {d.url: d for d in read(free_certs_source(db), FREE_CERTS_README)}

    assert by_url["https://about.gitlab.com/learn/"].title == "Gitlab: Free certification paths and badges"
    fortinet = by_url["https://training.fortinet.com/"]
    assert fortinet.metadata["organization"] == "Fortinet"
    assert "Security" in fortinet.metadata["tags"]


def test_list_records_are_certifications_awaiting_verification(db):
    source = free_certs_source(db)
    report = process(db, source, read(source, FREE_CERTS_README))
    assert report.created == 4

    rows = db.scalars(select(Opportunity).where(Opportunity.source_id == source.id)).all()
    assert {r.category for r in rows} == {"certifications"}
    assert {r.verification_status for r in rows} == {"needs_review"}
    fortinet = next(r for r in rows if r.source_url == "https://training.fortinet.com/" or "Fortinet" in r.title)
    detail = db.scalars(
        select(CredentialDetail).where(CredentialDetail.opportunity_id == fortinet.id)
    ).one()
    assert "cybersecurity" in detail.specializations


def test_a_readme_without_a_table_fails_rather_than_looking_empty(db):
    from app.ingestion.fetcher import FetchFailed

    with pytest.raises(FetchFailed):
        read(free_certs_source(db), "# Free-Certifications\n\nMoved to a new home.\n")


# --- Student discounts list -------------------------------------------------

DISCOUNTS_URL = "https://raw.githubusercontent.com/AchoArnold/discount-for-student-dev/master/README.md"
DISCOUNTS_README = """# Discount for Student Dev

  * [Web Hosting](#web-hosting)
  * [Design](#design)

## Web Hosting

* [Pageclip](https://pageclip.co/github-students) [FREE] - A server for static sites. Free basic plan while you are a student.

  * [Digital Ocean](https://www.digitalocean.com) [CREDIT] - $200 in hosting credit via the [Github Student Developer Pack](https://education.github.com/pack).

## Design and Photo Editing

* [Adobe Creative Cloud](https://www.adobe.com/creativecloud/buy/students.html) [DISCOUNT] - Students receive discounts on Adobe apps.
* [MATLAB](https://www.mathworks.com/academia.html) [MATLAB] - Not an offer tag.

## IDE and Code Editing

* [JetBrains IDE pack](https://www.jetbrains.com/community/education/) [FREE] - Free professional IDEs, including:
    * [CLion](https://www.jetbrains.com/clion/) [FREE] - A sub-feature, not a separate offer.
"""


def discounts_source(db):
    return api_source(
        db, name="Student developer discounts list",
        organization="AchoArnold/discount-for-student-dev", url=DISCOUNTS_URL,
        category="tech_benefits", authority="other_reputable_source", trust_level=3,
    )


def test_only_tagged_offers_are_read(db):
    documents = read(discounts_source(db), DISCOUNTS_README)
    assert [d.metadata["organization"] for d in documents] == [
        "Pageclip", "Digital Ocean", "Adobe Creative Cloud", "JetBrains IDE pack",
    ]  # no table-of-contents links, no untagged entries, no nested sub-features


def test_offer_tags_and_sections_map_to_cost_and_type(db):
    by_name = {d.metadata["organization"]: d for d in read(discounts_source(db), DISCOUNTS_README)}

    assert by_name["Pageclip"].metadata["cost_type"] == "free_for_students"
    assert by_name["Pageclip"].metadata["opportunity_type"] == "cloud_credits"
    assert by_name["Digital Ocean"].metadata["opportunity_type"] == "cloud_credits"
    assert by_name["Adobe Creative Cloud"].metadata["cost_type"] == "discounted"
    assert by_name["Adobe Creative Cloud"].title == "Adobe Creative Cloud — student discount"
    assert by_name["JetBrains IDE pack"].metadata["opportunity_type"] == "developer_tool"


def test_markdown_links_in_descriptions_become_plain_text(db):
    by_name = {d.metadata["organization"]: d for d in read(discounts_source(db), DISCOUNTS_README)}
    text = by_name["Digital Ocean"].text
    assert "Github Student Developer Pack" in text
    assert "](" not in text


def test_student_offers_become_tech_benefits_awaiting_verification(db):
    source = discounts_source(db)
    report = process(db, source, read(source, DISCOUNTS_README))
    assert report.created == 4

    rows = db.scalars(select(Opportunity).where(Opportunity.source_id == source.id)).all()
    assert {r.category for r in rows} == {"tech_benefits"}
    assert {r.verification_status for r in rows} == {"needs_review"}
    assert all(r.deadline is None for r in rows)
