"""Guards on the catalogue's honesty.

These assert the editorial rules in app/seed/data.py rather than any behaviour,
so a future edit cannot quietly reintroduce invented data.
"""
from __future__ import annotations

from urllib.parse import urlparse

import pytest

from app.models.enums import (
    Category,
    CostType,
    OpportunityType,
    VerificationMethod,
    VerificationStatus,
)
from app.seed.data import ALL_SEEDS
from app.seed.sources import SOURCES

ALLOWED_SEED_STATUSES = {
    VerificationStatus.CURATED.value,
    VerificationStatus.NEEDS_REVIEW.value,
}


def test_no_seed_record_invents_a_deadline():
    """Nothing in the catalogue publishes a standing date, so none may claim one."""
    dated = [s["title"] for s in ALL_SEEDS if s.get("deadline_days") is not None]
    assert dated == [], f"fabricated deadlines reintroduced: {dated}"


def test_no_seed_record_claims_its_source_was_checked():
    """SOURCE_CHECKED is reserved for records an automated check actually fetched."""
    overclaiming = [
        s["title"]
        for s in ALL_SEEDS
        if s.get("status") not in ALLOWED_SEED_STATUSES
    ]
    assert overclaiming == [], f"seed records overclaiming verification: {overclaiming}"


def test_every_seed_record_has_an_official_https_source():
    bad = [
        s["title"]
        for s in ALL_SEEDS
        if urlparse(s["url"]).scheme != "https" or urlparse(s["source_url"]).scheme != "https"
    ]
    assert bad == [], f"records without an https official source: {bad}"


def test_seed_categories_and_types_are_valid_enum_members():
    categories = {c.value for c in Category}
    types = {t.value for t in OpportunityType}
    costs = {c.value for c in CostType}
    for record in ALL_SEEDS:
        assert record["category"] in categories, record["title"]
        assert record["type"] in types, record["title"]
        assert record.get("cost", "free") in costs, record["title"]


def test_learning_platforms_are_not_labelled_certifications():
    """A catalogue of courses is not a credential — see the editorial rules."""
    platforms = {
        "Google Cloud Skills Boost",
        "Microsoft Learn Training and Certifications",
        "Cisco Networking Academy — Skills for All",
        "IBM SkillsBuild",
    }
    for record in ALL_SEEDS:
        if record["title"] in platforms:
            assert record["type"] == OpportunityType.LEARNING_PLATFORM.value, record["title"]


def test_records_have_substantive_descriptions():
    thin = [s["title"] for s in ALL_SEEDS if len(s["description"]) < 120]
    assert thin == [], f"records too thin to review: {thin}"


def test_records_are_distinguishable_for_deduplication():
    """Titles are unique, and no two records share both a title and a URL.

    A shared URL alone is legitimate: Google lists the Generation and Lime
    scholarships on one official page, and both are separate opportunities.
    Deduplication keys on title + organisation + URL, so distinct titles at a
    shared hub do not collide.
    """
    titles = [s["title"] for s in ALL_SEEDS]
    assert len(titles) == len(set(titles)), "duplicate titles"

    pairs = [(s["title"], s["url"]) for s in ALL_SEEDS]
    assert len(pairs) == len(set(pairs)), "duplicate title+url pairs"


def test_sources_that_disallow_automation_are_recorded_not_omitted():
    """A prohibition must be a fact in the system, not tribal knowledge."""
    blocked = [s for s in SOURCES if not s["robots_allowed"]]
    assert blocked, "expected at least one source registered as off-limits"
    for source in blocked:
        assert source["access_notes"], f"{source['name']} gives no reason"


@pytest.mark.parametrize("record", ALL_SEEDS, ids=lambda r: r["title"][:40])
def test_curated_records_name_their_organisation_and_summary(record):
    assert record["org"].strip()
    assert 10 <= len(record["summary"]) <= 400


def test_seeder_assigns_curation_as_the_verification_method(db):
    """Curated status and curation method must travel together."""
    from app.models.opportunity import Opportunity
    from app.seed.run import seed_opportunities, seed_sources, seed_users
    from sqlalchemy import select

    seed_users(db)
    sources = seed_sources(db)
    seed_opportunities(db, sources)
    db.flush()

    rows = db.scalars(select(Opportunity)).all()
    assert rows
    for row in rows:
        if row.verification_status == VerificationStatus.CURATED.value:
            assert row.verification_method == VerificationMethod.CURATION.value
            assert row.verified_by == "zenkai-curation"
        else:
            assert row.verification_method == VerificationMethod.NONE.value
            assert row.verified_by is None
        # Nothing in the catalogue may claim an automated source check.
        assert row.verification_status != VerificationStatus.SOURCE_CHECKED.value
