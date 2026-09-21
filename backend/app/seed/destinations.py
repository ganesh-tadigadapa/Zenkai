"""Destination overrides, from the link audit of 2026-09-20.

Every URL here was fetched before being adopted. Where a host returns 200 for
any path — several are single-page apps that do — a 200 proves nothing, so
those candidates were rejected rather than trusted.

Records absent from both tables keep their catalogue URL as the direct
destination, because it already points at the exact page where a student acts.
"""
from __future__ import annotations

#: Records whose URL is a hub, listing or search page rather than somewhere a
#: student can act. They get NO direct destination: the interface falls back to
#: the official source and says so. Values are the reason, for the reviewer.
NO_DIRECT_DESTINATION: dict[str, str] = {
    "Generation Google Scholarship": (
        "buildyourfuture.withgoogle.com/scholarships lists several scholarships. "
        "Per-scholarship paths return 200 for any path on that host, so none "
        "could be verified."
    ),
    "Google Lime Scholarship": (
        "Same shared hub as the Generation scholarship; no per-scholarship URL "
        "could be verified."
    ),
    "Grace Hopper Celebration Student Scholarship": (
        "ghc.anitab.org/attend/scholarships/ redirects in a loop. No working "
        "scholarships page was found; the conference site is the best anchor."
    ),
    "Adobe Research Women-in-Technology Scholarship": (
        "research.adobe.com/scholarship/ now returns 404, as do the obvious "
        "alternatives. Needs a human to find the current page."
    ),
    "NASA Space Apps Challenge": (
        "spaceappschallenge.org refused connections from the audit client, so "
        "nothing could be confirmed. Likely reachable in a browser."
    ),
}

#: Corrections where the audit found a broken URL AND a verified replacement.
#: ``url`` is the direct destination; ``source_url`` the authoritative page.
URL_FIXES: dict[str, dict[str, str]] = {
    "Major League Hacking Season": {
        # mlh.io/seasons returns 404. /events redirects to the current season
        # schedule, so it does not go stale the way a year-pinned path would.
        "url": "https://mlh.io/events",
        "source_url": "https://mlh.io/",
        "note": "seasons path 404s; /events resolves to the current season schedule",
    },
    "Reliance Foundation Undergraduate Scholarships": {
        # reliancefoundation.org/scholarships 404s. The scholarships subdomain
        # root returns 200 and its title is "Reliance Foundation Scholarships".
        "url": "https://scholarships.reliancefoundation.org/",
        "source_url": "https://scholarships.reliancefoundation.org/",
        "note": "main-site path 404s; scholarships subdomain confirmed by page title",
    },
    "Adobe Research Women-in-Technology Scholarship": {
        # The scholarship page is gone; anchor on the research site root, which
        # resolves. No direct destination — see NO_DIRECT_DESTINATION above.
        "url": "https://research.adobe.com/",
        "source_url": "https://research.adobe.com/",
        "note": "scholarship path 404s; anchored on the Adobe Research root",
    },
    "Grace Hopper Celebration Student Scholarship": {
        "url": "https://ghc.anitab.org/",
        "source_url": "https://ghc.anitab.org/",
        "note": "attend/scholarships/ redirects in a loop; conference root resolves",
    },
    "Google STEP Internship": {
        # The old apply URL was a careers *search results* page — exactly the
        # experience this work exists to remove. The programme page is the
        # right destination and resolves.
        "url": "https://buildyourfuture.withgoogle.com/programs/step",
        "source_url": "https://buildyourfuture.withgoogle.com/programs/step",
        "note": "replaced a careers search-results URL with the programme page",
    },
}

#: Hosts that rejected the audit client with 403. These are bot protections,
#: not broken links: a student's browser reaches them. Recorded so a reviewer
#: is not sent chasing pages that work.
BLOCKED_TO_BOTS: set[str] = {
    "Autodesk Education Access",
    "Oracle Cloud Free Tier",
    "Tableau for Students",
    "Bloomberg Engineering Internship",
}
