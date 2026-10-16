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
            "DISABLED. Verified 2026-10-15: the feed serves entries again, but "
            "they are long-form articles, and a single phrase in passing "
            "(\"mentorship programme\", \"call for proposals\") carries them "
            "through the relevance gate — 2 of 25 entries on a trial run, "
            "neither an opportunity. Re-enable once the gate weighs body-only "
            "signals in long posts."
        ),
        active=False,
    ),
    dict(
        # Verified 2026-10-15: RSS, 200. Mostly product news, which the
        # relevance gate rejects; it also announces developer programmes,
        # student challenges and fellowships.
        name="Google Developers Blog",
        organization="Google",
        url="https://developers.googleblog.com/feeds/posts/default",
        official_url="https://developers.googleblog.com/",
        source_type="rss",
        category="programs",
        authority="official_organization",
        discovery_method="rss",
        check_frequency="normal",
        trust_level=5,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes="RSS feed published by Google for syndication.",
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
        # The calendar moves to a new path each season; update the year when
        # MLH opens the next one. Read through the mlh page adapter.
        name="MLH Events",
        organization="Major League Hacking",
        url="https://www.mlh.com/seasons/2027/events",
        official_url="https://www.mlh.com/",
        source_type="web",
        category="hackathons",
        authority="established_platform",
        discovery_method="public_webpage",
        check_frequency="normal",
        trust_level=4,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes=(
            "Season calendar page, permitted by robots.txt. One request: the page "
            "embeds its event list as JSON, which the mlh adapter reads. Event "
            "sub-pages and event websites are never fetched."
        ),
    ),
    dict(
        name="Devpost Hackathons",
        organization="Devpost",
        url="https://devpost.com/api/hackathons?status[]=upcoming&status[]=open",
        official_url="https://devpost.com/hackathons",
        source_type="official_api",
        category="hackathons",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="high",
        trust_level=4,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes=(
            "Public JSON endpoint backing Devpost's own hackathon listing; "
            "robots.txt does not disallow it. Open and upcoming events only, "
            "paginated at 9 per page and capped by the connector."
        ),
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
        # Verified 2026-10-15: robots.txt explicitly allows /api/public/*.
        # `oppstatus=open` returns only listings with registration open.
        name="Unstop internships",
        organization="Unstop",
        url="https://unstop.com/api/public/opportunity/search-result?opportunity=internships&oppstatus=open&per_page=30",
        official_url="https://unstop.com/internships",
        source_type="official_api",
        category="internships",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="high",
        trust_level=3,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes=(
            "Public JSON endpoint behind Unstop's own listing pages; robots.txt "
            "allows /api/public/*. A marketplace — organisers post their own "
            "listings — so trust is below an official issuer's."
        ),
    ),
    dict(
        name="Unstop hackathons",
        organization="Unstop",
        url="https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&oppstatus=open&per_page=30",
        official_url="https://unstop.com/hackathons",
        source_type="official_api",
        category="hackathons",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="high",
        trust_level=3,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes="Same endpoint as Unstop internships, filtered to open hackathons.",
    ),
    dict(
        name="Unstop scholarships",
        organization="Unstop",
        url="https://unstop.com/api/public/opportunity/search-result?opportunity=scholarships&oppstatus=open&per_page=30",
        official_url="https://unstop.com/scholarships",
        source_type="official_api",
        category="scholarships",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="normal",
        trust_level=3,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes="Same endpoint as Unstop internships, filtered to open scholarships.",
    ),
    dict(
        # Verified 2026-10-15: 200, ~13 MB, 17,000+ postings, 4,800 active.
        name="SimplifyJobs internships",
        organization="SimplifyJobs",
        url="https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json",
        official_url="https://github.com/SimplifyJobs/Summer2026-Internships",
        source_type="official_api",
        category="internships",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="high",
        trust_level=4,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes=(
            "Data file of a public GitHub repository, served from "
            "raw.githubusercontent.com for exactly this kind of reading. The "
            "1,000 newest active postings are taken; links go to employers' own "
            "application pages."
        ),
    ),
    dict(
        # Verified 2026-10-15: 200, 83 offer cards, no robots.txt rules.
        name="GitHub Student Pack offers",
        organization="GitHub",
        url="https://education.github.com/pack/offers",
        official_url="https://education.github.com/pack",
        source_type="web",
        category="tech_benefits",
        authority="official_organization",
        discovery_method="public_webpage",
        check_frequency="low",
        trust_level=5,
        check_frequency_minutes=1440,
        robots_allowed=True,
        access_notes=(
            "Official offers page. One request; each partner card becomes a "
            "benefit. Partner sites are never fetched."
        ),
    ),
    dict(
        # Verified 2026-10-16: 200, 37 Applied Skills credentials. Same public
        # catalogue API as the certifications source, scoped to one collection.
        name="Microsoft Learn Applied Skills",
        organization="Microsoft",
        url="https://learn.microsoft.com/api/catalog/?locale=en-us&type=appliedSkills",
        official_url="https://learn.microsoft.com/credentials/applied-skills/",
        source_type="official_api",
        category="certifications",
        authority="official_issuer",
        discovery_method="official_api",
        check_frequency="normal",
        trust_level=5,
        check_frequency_minutes=1440,
        priority=85,
        robots_allowed=True,
        access_notes=(
            "Public catalogue API, permitted by robots.txt. Applied Skills are "
            "scenario-based credentials earned through a lab assessment. Cost "
            "is not published by the API, so it stays UNKNOWN."
        ),
    ),
    dict(
        # Verified 2026-10-16: 200, 733 open competitions. Same endpoint as the
        # other Unstop sources; robots.txt allows /api/public/*.
        name="Unstop competitions",
        organization="Unstop",
        url="https://unstop.com/api/public/opportunity/search-result?opportunity=competitions&oppstatus=open&per_page=30",
        official_url="https://unstop.com/competitions",
        source_type="official_api",
        category="hackathons",
        authority="established_platform",
        discovery_method="official_api",
        check_frequency="high",
        trust_level=3,
        check_frequency_minutes=360,
        robots_allowed=True,
        access_notes=(
            "Same endpoint as Unstop internships, filtered to open competitions: "
            "case studies, quizzes, coding and business contests."
        ),
    ),
    dict(
        # Verified 2026-10-16: 200, 126 rows, MIT licence. About 100 rows are
        # still open-ended; the adapter drops rows whose offer has ended.
        name="Free Certifications list",
        organization="ArslanYM/Free-Certifications",
        url="https://raw.githubusercontent.com/ArslanYM/Free-Certifications/main/README.md",
        official_url="https://github.com/ArslanYM/Free-Certifications",
        source_type="official_api",
        category="certifications",
        authority="other_reputable_source",
        discovery_method="official_api",
        check_frequency="low",
        trust_level=3,
        check_frequency_minutes=1440,
        robots_allowed=True,
        access_notes=(
            "Community-maintained list in a public GitHub repository, read from "
            "raw.githubusercontent.com. Useful for discovery only: records stay "
            "'Needs verification' and link to each provider's own page."
        ),
    ),
    dict(
        # Verified 2026-10-15: RSS, 200. Scholarships, fellowships and
        # competitions worldwide; the relevance gate filters the rest.
        name="Opportunity Desk",
        organization="Opportunity Desk",
        url="https://opportunitydesk.org/feed/",
        official_url="https://opportunitydesk.org/",
        source_type="rss",
        category="scholarships",
        authority="other_reputable_source",
        discovery_method="rss",
        check_frequency="normal",
        trust_level=3,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes=(
            "Aggregator RSS feed published for syndication. Secondary source: "
            "each record links to the aggregator's post, which names the "
            "official programme."
        ),
    ),
    dict(
        name="Opportunities for Youth",
        organization="Opportunities for Youth",
        url="https://www.opportunitiesforyouth.org/feed/",
        official_url="https://www.opportunitiesforyouth.org/",
        source_type="rss",
        category="scholarships",
        authority="other_reputable_source",
        discovery_method="rss",
        check_frequency="normal",
        trust_level=3,
        check_frequency_minutes=720,
        robots_allowed=True,
        access_notes=(
            "DISABLED. Verified 2026-10-15: the feed answers HTTP 403 to "
            "ZenkaiBot. That is the site declining automated reading, so it is "
            "not fetched."
        ),
        active=False,
    ),
    dict(
        name="Manual editorial submissions",
        url="https://getzenkai.vercel.app/internal/manual",
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
