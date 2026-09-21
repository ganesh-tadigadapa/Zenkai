"""Sources registered for the future ingestion pipeline.

Every entry is an official page or feed published by the organisation itself.
``robots_allowed`` reflects whether we have established that automated access is
permitted; ``access_notes`` records what we know. Connectors refuse to fetch a
source where this is False.
"""
from __future__ import annotations

SOURCES = [
    dict(
        name="GitHub Education",
        url="https://education.github.com/pack",
        source_type="web",
        category="tech_benefits",
        authority="official_organization",
        discovery_method="public_webpage",
        check_frequency="high",
        trust_level=5,
        check_frequency_minutes=1440,
        robots_allowed=True,
        access_notes="Official programme page. Single-page fetch only; no crawling of partner sites.",
    ),
    dict(
        name="Google Open Source Blog",
        url="https://opensource.googleblog.com/feeds/posts/default",
        source_type="atom",
        category="programs",
        authority="official_organization",
        discovery_method="atom",
        check_frequency="normal",
        trust_level=5,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes=(
            "DISABLED. Verified 2026-09-20: this feed path returns 404, as does "
            "/atom.xml. Needs a working URL before it is re-enabled."
        ),
        active=False,
    ),
    dict(
        name="AWS What's New",
        url="https://aws.amazon.com/about-aws/whats-new/recent/feed/",
        source_type="rss",
        category="tech_benefits",
        authority="official_issuer",
        discovery_method="rss",
        check_frequency="high",
        trust_level=5,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes="Public RSS feed published by AWS for syndication.",
    ),
    dict(
        name="Microsoft Azure Updates",
        url="https://azurecomcdn.azureedge.net/en-us/updates/feed/",
        source_type="rss",
        category="tech_benefits",
        authority="official_issuer",
        discovery_method="rss",
        check_frequency="normal",
        trust_level=5,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes=(
            "DISABLED. Verified 2026-09-20: returns 200 but serves no feed items. "
            "Needs a working URL before it is re-enabled."
        ),
        active=False,
    ),
    dict(
        name="MLH Events",
        url="https://mlh.io/seasons",
        source_type="web",
        category="hackathons",
        authority="established_platform",
        discovery_method="public_webpage",
        check_frequency="normal",
        trust_level=4,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes="Season listing page. Fetch the listing only; do not enumerate event sub-pages.",
    ),
    dict(
        name="Devpost Hackathons",
        url="https://devpost.com/api/hackathons",
        source_type="official_api",
        category="hackathons",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="high",
        trust_level=4,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes="Public JSON endpoint backing the hackathon listing. Confirm terms of use before enabling.",
    ),
    dict(
        name="Outreachy",
        url="https://www.outreachy.org/",
        source_type="web",
        category="internships",
        authority="official_organization",
        discovery_method="public_webpage",
        check_frequency="low",
        trust_level=5,
        check_frequency_minutes=1440,
        robots_allowed=True,
        access_notes="Official programme site; cohort dates published openly.",
    ),
    dict(
        # Verified 2026-09-20: public JSON catalogue behind Microsoft's own
        # certification pages. robots.txt permits /api/. Carries 151
        # certifications and 145 exams with levels, roles and exam codes.
        # It does NOT publish price, proctoring or validity, so those stay
        # UNKNOWN on every record it produces.
        name="Microsoft Learn catalogue",
        organization="Microsoft",
        # Scoped to the two collections the adapter reads: 440KB rather
        # than the 14MB full catalogue, which is politer and stays well
        # inside the fetcher's size guard.
        url="https://learn.microsoft.com/api/catalog/?locale=en-us&type=certifications,exams",
        official_url="https://learn.microsoft.com/credentials/",
        source_type="official_api",
        category="certifications",
        authority="official_issuer",
        discovery_method="official_api",
        check_frequency="normal",
        trust_level=5,
        check_frequency_minutes=1440,
        priority=90,
        robots_allowed=True,
        access_notes=(
            "Public catalogue API, permitted by robots.txt. Read through the "
            "microsoft-learn adapter, which maps only the fields the API "
            "carries and leaves cost, proctoring and validity UNKNOWN."
        ),
    ),
    dict(
        # Verified 2026-09-20: Atom, 200, 43 entries, robots.txt absent so
        # nothing is disallowed. Carries the cohort announcements themselves,
        # which the programme homepage does not.
        name="Outreachy announcements",
        organization="Software Freedom Conservancy",
        url="https://www.outreachy.org/blog/feed/",
        official_url="https://www.outreachy.org/",
        source_type="atom",
        category="internships",
        authority="official_organization",
        discovery_method="atom",
        check_frequency="normal",
        trust_level=5,
        check_frequency_minutes=1440,
        robots_allowed=True,
        access_notes=(
            "Atom feed published for syndication. No robots.txt on the host, so "
            "no rule disallows it. Announces each cohort's application window."
        ),
    ),
    dict(
        name="Google Summer of Code",
        url="https://summerofcode.withgoogle.com/",
        source_type="web",
        category="programs",
        authority="official_organization",
        discovery_method="public_webpage",
        check_frequency="low",
        trust_level=5,
        check_frequency_minutes=1440,
        robots_allowed=True,
        access_notes="Official programme site. Timeline page carries each year's dates.",
    ),
    dict(
        name="Manual editorial submissions",
        url="https://zenkai.dev/internal/manual",
        source_type="manual",
        category=None,
        authority="official_organization",
        discovery_method="manual",
        check_frequency="low",
        trust_level=5,
        check_frequency_minutes=10080,
        robots_allowed=True,
        access_notes="Records entered by a human reviewer through /admin. No fetching involved.",
    ),
    dict(
        name="LinkedIn job postings",
        url="https://www.linkedin.com/jobs/",
        source_type="web",
        category="internships",
        authority="other_reputable_source",
        discovery_method="unknown",
        check_frequency="low",
        trust_level=2,
        check_frequency_minutes=1440,
        robots_allowed=False,
        access_notes=(
            "DISABLED. LinkedIn's terms prohibit automated collection. Registered here only so "
            "the pipeline has an explicit record of a source it must never fetch."
        ),
    ),
]
